import logging

_logger = logging.getLogger(__name__)


def _apply_structured_communication(env):
    """Make sale journals number invoices with their country's structured communication.

    Bank transfers are reconciled on the communication, so the payment reference that
    ends up in the mail and in the SEPA QR-code has to be a machine readable one. Odoo
    only picks the localised model (``be`` -> ``+++000/0000/00000+++``) for journals it
    creates itself, so journals that predate the localisation keep the human readable
    ``INV/2026/00001``. Only journals still on that default are touched.
    """
    journals = env['account.journal'].sudo().search([('type', '=', 'sale')])
    if not journals:
        return
    available = dict(journals._fields['invoice_reference_model']._description_selection(env))
    for journal in journals:
        country_code = (journal.company_id.country_id.code or '').lower()
        if journal.invoice_reference_model != 'odoo' or country_code not in available:
            continue
        journal.invoice_reference_model = country_code
        journal.invoice_reference_type = 'invoice'
        _logger.info(
            "sterrenboom: journal %s now numbers invoices with the %s structured communication",
            journal.code, country_code,
        )


def post_init_hook(env):
    _apply_structured_communication(env)
