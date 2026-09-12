from odoo import models


class AccountMove(models.Model):
    """Expose the bank transfer details of a registration invoice to the website."""

    _inherit = 'account.move'

    def _sterrenboom_payment_bank(self):
        """Account to transfer to: the one on the invoice, else the company's first."""
        self.ensure_one()
        return self.partner_bank_id or self.company_id.partner_id.bank_ids[:1]

    def _sterrenboom_payment_qr_code(self):
        """SEPA credit transfer QR-code as a base64 data URI, or ``False``.

        Same code Odoo prints on an invoice PDF: a banking app scans it and pre-fills
        beneficiary, amount and structured communication. Returns ``False`` when the
        company has no (SEPA) bank account or nothing is left to pay, so the caller can
        fall back to the written instructions.
        """
        self.ensure_one()
        bank = self._sterrenboom_payment_bank()
        if not bank or self.currency_id.is_zero(self.amount_residual):
            return False
        return bank.build_qr_code_base64(
            self.amount_residual,
            self.payment_reference or self.name,
            self.payment_reference,
            self.currency_id,
            self.partner_id,
            silent_errors=True,
        ) or False

    def _sterrenboom_payment_values(self):
        """Everything the confirmation page and the payment mail need, in one dict."""
        self.ensure_one()
        return {
            'invoice': self,
            'bank': self._sterrenboom_payment_bank(),
            'amount': self.amount_residual,
            'currency': self.currency_id,
            'communication': self.payment_reference or self.name,
            'qr_code': self._sterrenboom_payment_qr_code(),
        }
