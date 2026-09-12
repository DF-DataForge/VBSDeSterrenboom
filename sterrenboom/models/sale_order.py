import logging

from odoo import models
from odoo.exceptions import AccessError, RedirectWarning, UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Turn a website event registration order into a posted customer invoice."""

    _inherit = 'sale.order'

    def _sterrenboom_invoice_registrations(self):
        """Confirm this order and post its customer invoice, and return that invoice.

        The committee is paid by bank transfer, not through the website, so the order is
        confirmed and invoiced right after the visitor fills in the attendee details.
        Posting the invoice is what gives the attendee a structured communication and
        what lets Accounting reconcile the incoming transfer on its own.

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
