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
        """Register the attendees of this order and mail their tickets in one mail.

        For the committee to click once the bank transfer for the invoice has been
        processed; nothing triggers it automatically. The attendees are registered
        without Odoo's per-attendee confirmation mail (the event's "After each
        registration" communication is marked as done for them instead), and one mail
        per order goes to the customer with every attendee's ticket PDF attached. The
        mail is delivered immediately and the outcome reported in a notification. A
        later click sends the tickets again.
        """
        self.ensure_one()
        registrations = self._sterrenboom_registrations()
        if not registrations:
            raise UserError(_("There are no attendees to send tickets to on %s.", self.name))
        if self.state != 'sale':
            raise UserError(_("Confirm %s before sending its tickets.", self.name))

        # Recompute / write the attendee state without running the event's
        # communication: the tickets go out in the single mail below.
        registrations = registrations.with_context(sterrenboom_skip_event_mails=True)
        if self.sterrenboom_tickets_on_hold:
            self.sterrenboom_tickets_on_hold = False
            registrations.flush_recordset(['state'])
        registrations.filtered(lambda reg: reg.state == 'draft').action_confirm()
        registrations._sterrenboom_mark_event_mails_done()

        mail = self._sterrenboom_send_tickets_mail(registrations)
        # Deliver now, so the committee sees a bounce here rather than in the mail queue.
        mail.send(auto_commit=False, raise_exception=False)

        self.sterrenboom_tickets_sent_date = fields.Datetime.now()
        names = ', '.join(registrations.mapped('display_name'))
        if mail.exists() and mail.state == 'exception':
            body = _(
                "Sending the tickets to %(email)s failed: %(reason)s. Attendees: %(names)s.",
                email=mail.email_to, names=names,
                reason=mail.failure_reason or mail.failure_type or _("unknown reason"),
            )
            self._message_log(body=body)
            return self._sterrenboom_notify(_("Tickets not sent"), body, 'danger')
        body = _(
            "Tickets for %(count)s attendee(s) sent to %(email)s: %(names)s.",
            count=len(registrations), email=mail.email_to, names=names,
        )
        # A plain log line: the mail itself already shows in the chatter with the PDF,
        # and a note with attachments would look like a second tickets mail (and could
        # notify followers).
        self._message_log(body=body)
        return self._sterrenboom_notify(_("Tickets sent"), body, 'success')

    def _sterrenboom_tickets_attachment(self, registrations):
        """One PDF with all the attendees' full-page tickets, attached to this order."""
        pdf, _report_type = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'event.action_report_event_registration_full_page_ticket', registrations.ids,
        )
        events = ', '.join(registrations.event_id.mapped('name'))
        return self.env['ir.attachment'].sudo().create({
            'name': f"Tickets - {events} - {self.name}.pdf".replace('/', '-'),
            'type': 'binary',
            'raw': pdf,
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        })

    def _sterrenboom_send_tickets_mail(self, registrations):
        """Queue the tickets mail for this order and return the ``mail.mail``.

        Addressed to the customer (the person who booked); attendee addresses are the
        fallback when the customer has none. All tickets go in one PDF.
        """
        self.ensure_one()
        template = self.env.ref('sterrenboom.mail_template_tickets')
        emails = [self.partner_id.email_formatted] if self.partner_id.email else \
            registrations._sterrenboom_payment_emails()
        if not emails:
            raise UserError(_(
                "Neither the customer nor the attendees of %s have an email address.", self.name,
            ))
        attachment = self._sterrenboom_tickets_attachment(registrations)
        mail_id = template.sudo().send_mail(
            self.id,
            force_send=False,
            email_values={
                'email_to': ','.join(emails),
                'attachment_ids': [(4, attachment.id)],
            },
        )
        return self.env['mail.mail'].sudo().browse(mail_id)

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
