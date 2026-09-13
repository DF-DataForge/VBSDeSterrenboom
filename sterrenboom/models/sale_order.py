import logging

from odoo import _, fields, models
from odoo.exceptions import AccessError, RedirectWarning, UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Turn a website event registration order into a posted customer invoice."""

    _inherit = 'sale.order'

    sterrenboom_tickets_on_hold = fields.Boolean(
        string='Tickets on Hold',
        copy=False,
        help="Set by the website registration flow. While it is set the attendees stay "
             "Unconfirmed and receive no ticket; click Send Tickets once the bank transfer "
             "has been processed.",
    )
    sterrenboom_tickets_sent_date = fields.Datetime(
        string='Tickets Sent On',
        copy=False,
        readonly=True,
    )

    def _sterrenboom_registrations(self):
        """The attendees booked on these orders, cancelled ones excluded."""
        return self.order_line.registration_ids.filtered(lambda reg: reg.state != 'cancel')

    def _sterrenboom_invoice_registrations(self):
        """Confirm this order and post its customer invoice, and return that invoice.

        The committee is paid by bank transfer, not through the website, so the order is
        confirmed and invoiced right after the visitor fills in the attendee details.
        Posting the invoice is what gives the attendee a structured communication and
        what lets Accounting reconcile the incoming transfer on its own.

        The tickets are put on hold before the order is confirmed: confirming an order
        normally registers its attendees at once, which mails them their tickets. Here
        they stay Unconfirmed until the committee clicks *Send Tickets* on the order.

        Idempotent: an order that already carries an invoice is not invoiced twice.
        Returns an empty recordset when nothing can be invoiced.
        """
        self.ensure_one()
        empty = self.env['account.move']
        if self.state == 'cancel' or self.currency_id.is_zero(self.amount_total):
            # Nothing to pay: free events keep the plain website_event flow.
            return empty
        try:
            if self.state in ('draft', 'sent'):
                self.sterrenboom_tickets_on_hold = True
                self.action_confirm()
            invoice = self.invoice_ids.filtered(
                lambda move: move.move_type == 'out_invoice' and move.state != 'cancel'
            )[:1]
            if not invoice:
                invoiceable = self._get_invoiceable_lines().filtered(
                    lambda line: not line.display_type
                )
                if not invoiceable:
                    _logger.warning(
                        "sterrenboom: sale order %s has no invoiceable line, no invoice created. "
                        "Check the 'Invoicing Policy' of the ticket products.", self.name,
                    )
                    return empty
                invoice = self._create_invoices()
            if invoice.state == 'draft':
                invoice.action_post()
            return invoice
        except (AccessError, RedirectWarning, UserError, ValidationError):
            # Never lose a registration over an accounting misconfiguration: the visitor
            # still gets their confirmation page, the committee sees the order.
            # RedirectWarning is raised by account when the company bank account has not
            # been marked as trusted, and it is not a UserError subclass.
            _logger.exception("sterrenboom: could not invoice sale order %s", self.name)
            return empty

    def action_sterrenboom_send_tickets(self):
        """Register the attendees of this order and mail them their tickets, now.

        For the committee to click once the bank transfer for the invoice has been
        processed; nothing triggers it automatically. The first click releases the
        hold set by the website flow, which registers the attendees and runs the
        event's "After each registration" communication (Odoo's confirmation mail with
        the ticket PDF). Attendees that communication does not cover, and every later
        click (a resend, e.g. after a bounce), get that same confirmation mail sent
        directly. The mails are delivered immediately instead of waiting for the mail
        queue, and the outcome is reported in a notification.
        """
        self.ensure_one()
        registrations = self._sterrenboom_registrations()
        if not registrations:
            raise UserError(_("There are no attendees to send tickets to on %s.", self.name))
        if self.state != 'sale':
            raise UserError(_("Confirm %s before sending its tickets.", self.name))

        Mail = self.env['mail.mail'].sudo()
        mail_domain = [('model', '=', 'event.registration'), ('res_id', 'in', registrations.ids)]
        known_mail_ids = set(Mail.search(mail_domain).ids)

        if self.sterrenboom_tickets_on_hold:
            self.sterrenboom_tickets_on_hold = False
            # Recompute the attendee state now: that is what runs the event's
            # communication for the attendees it covers.
            registrations.flush_recordset(['state'])
        registrations.filtered(lambda reg: reg.state == 'draft').action_confirm()

        # Whoever the communication did not just mail gets the confirmation directly:
        # events without such a communication, and resends.
        new_mails = Mail.search(mail_domain).filtered(lambda mail: mail.id not in known_mail_ids)
        mailed = registrations.filtered(lambda reg: reg.id in set(new_mails.mapped('res_id')))
        (registrations - mailed)._sterrenboom_send_ticket_mail()
        new_mails = Mail.search(mail_domain).filtered(lambda mail: mail.id not in known_mail_ids)

        # Deliver now, so the committee sees a bounce here rather than in the mail queue.
        new_mails.send(auto_commit=False, raise_exception=False)
        failed = new_mails.exists().filtered(lambda mail: mail.state == 'exception')
        sent_count = len(new_mails) - len(failed)

        self.sterrenboom_tickets_sent_date = fields.Datetime.now()
        names = ', '.join(registrations.mapped('display_name'))
        if failed:
            reasons = '; '.join(
                f"{mail.email_to or mail.recipient_ids.mapped('email')}: "
                f"{mail.failure_reason or mail.failure_type or _('unknown reason')}"
                for mail in failed
            )
            body = _(
                "Tickets: %(sent)s mail(s) sent, %(failed)s failed (%(reasons)s). "
                "Attendees: %(names)s.",
                sent=sent_count, failed=len(failed), reasons=reasons, names=names,
            )
            self.message_post(body=body)
            return self._sterrenboom_notify(_("Tickets partly sent"), body, 'warning')
        body = _(
            "Tickets sent to %(count)s attendee(s) in %(mails)s mail(s): %(names)s.",
            count=len(registrations), mails=sent_count, names=names,
        )
        self.message_post(body=body)
        return self._sterrenboom_notify(_("Tickets sent"), body, 'success')

    def _sterrenboom_notify(self, title, message, level):
        """Sticky popup shown to the user who clicked the button."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': level,
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
