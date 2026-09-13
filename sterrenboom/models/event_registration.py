import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class EventRegistration(models.Model):
    """Tie website registrations to the invoice the attendee has to transfer money for."""

    _inherit = 'event.registration'

    @api.depends('sale_order_id.sterrenboom_tickets_on_hold')
    def _compute_registration_status(self):
        """Keep attendees of an order with tickets on hold Unconfirmed.

        ``event_sale`` registers an attendee as soon as their order is confirmed, and
        registering is what mails the ticket and unlocks its download. The website flow
        confirms the order right away to invoice it, so the hold set there keeps the
        attendee Unconfirmed (and "to pay") until the committee releases it.
        """
        super()._compute_registration_status()
        held = self.filtered(
            lambda reg: reg.state == 'open' and reg.sale_order_id.sterrenboom_tickets_on_hold
        )
        held.state = 'draft'
        held.sale_status = 'to_pay'

    def _sterrenboom_send_ticket_mail(self):
        """Queue Odoo's registration confirmation, with the ticket PDF, to these attendees.

        Same template the event's "After each registration" communication uses, so a
        resend or an event without that communication produces the identical mail.
        Cancelled and unconfirmed attendees are skipped.
        """
        template = self.env.ref('event.event_subscription', raise_if_not_found=False)
        if not template:
            return
        for registration in self.filtered(lambda reg: reg.state in ('open', 'done')):
            template.sudo().send_mail(registration.id, force_send=False)

    def _sterrenboom_invoice(self):
        """The posted customer invoice covering these registrations, if there is one."""
        invoices = self.sale_order_id.invoice_ids.filtered(
            lambda move: move.move_type == 'out_invoice' and move.state == 'posted'
        )
        return invoices.sorted('id')[:1]

    def _sterrenboom_payment_values(self):
        """Bank transfer details for the confirmation page, empty when nothing is due."""
        invoice = self._sterrenboom_invoice()
        if not invoice or invoice.currency_id.is_zero(invoice.amount_residual):
            return {}
        return invoice._sterrenboom_payment_values()

    def _sterrenboom_payment_emails(self):
        """Addresses to mail the payment instructions to, attendees first."""
        emails = list(dict.fromkeys(
            registration.email for registration in self if registration.email
        ))
        if emails:
            return emails
        partner = self.sale_order_id.partner_id
        return [partner.email] if partner.email else []

    def _sterrenboom_send_payment_instructions(self, force_send=True):
        """Mail the attendees how to pay, with the invoice's structured communication.

        Returns the ``mail.mail`` records created, so callers can tell whether anything
        was sent. Failures are logged rather than raised: a visitor who registered
        successfully must not see an error page because SMTP is down. Pass
        ``force_send=False`` to leave the mail on the queue for the mail cron.
        """
        invoice = self._sterrenboom_invoice()
        if not invoice or invoice.currency_id.is_zero(invoice.amount_residual):
            return self.env['mail.mail']
        template = self.env.ref(
            'sterrenboom.mail_template_registration_payment', raise_if_not_found=False
        )
        emails = self._sterrenboom_payment_emails()
        if not template or not emails:
            return self.env['mail.mail']
        try:
            return template.sudo().send_mail_batch(
                [invoice.id],
                force_send=force_send,
                email_values={'email_to': ','.join(emails)},
            )
        except Exception:  # a failed mail must never fail the registration
            _logger.exception(
                "sterrenboom: could not send payment instructions for invoice %s", invoice.name
            )
            return self.env['mail.mail']
