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
        """Register the attendees of these orders and mail them their tickets.

        For the committee to click once the bank transfer for the invoice has been
        processed; nothing triggers it automatically. Releasing the hold recomputes the
        attendees to Registered, which runs the event's "After each registration"
        communication: Odoo's confirmation mail with the ticket PDF attached. Events
        without such a communication get that mail sent directly.
        """
        for order in self:
            if not order.sterrenboom_tickets_on_hold:
                raise UserError(_(
                    "The tickets of %(order)s are not on hold: they were either sent "
                    "already or the order was not booked on the website.",
                    order=order.name,
                ))
            registrations = order._sterrenboom_registrations()
            if not registrations:
                raise UserError(_("There are no attendees to send tickets to on %s.", order.name))
            order.sterrenboom_tickets_on_hold = False
            # Recompute the attendee state now: that is what runs the event's
            # communication, and the fallback below needs the final state.
            registrations.flush_recordset(['state'])
            registrations._sterrenboom_send_ticket_mail_fallback()
            order.sterrenboom_tickets_sent_date = fields.Datetime.now()
            order.message_post(body=_(
                "Tickets sent to %(count)s attendee(s): %(names)s.",
                count=len(registrations),
                names=', '.join(registrations.mapped('display_name')),
            ))
        return True
