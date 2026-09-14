import logging

from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_normalize

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


def _apply_outgoing_mail_identity(env):
    """Send every outgoing mail from the company mailbox.

    The committee's SMTP provider only accepts mail whose From is the mailbox itself,
    while Odoo mails on behalf of OdooBot (activity assignments), the public website
    user or whoever is responsible: those bounced. Odoo's own answer is two settings
    that this configures from the company email address (e.g. ``oc@example.org``):

    * a ``mail.alias.domain`` for ``example.org`` whose *Default From*, catchall and
      bounce aliases are all ``oc``: any sender the outgoing server does not accept
      is rewritten to ``oc@example.org`` (the author's name is kept), replies and
      bounces come back to that same mailbox;
    * *FROM Filtering* = ``oc@example.org`` on outgoing mail servers that have none,
      which is what makes the rewrite kick in for every other sender.

    A *personal* outgoing server for that mailbox (one with an owner, as Odoo creates
    for a Gmail or Outlook account connected from a user's preferences) only serves
    mails that user authors, so it is made company-wide first.

    Companies without an email address, or already using an alias domain for another
    domain name, are left alone. Aliases the committee changed by hand are kept. Runs at
    install, on upgrade and whenever a company email address is set.
    """
    AliasDomain = env['mail.alias.domain'].sudo()
    IrMailServer = env['ir.mail_server'].sudo()
    for company in env['res.company'].sudo().search([]):
        email = email_normalize(company.email or '')
        if not email:
            _logger.warning(
                "sterrenboom: company %s has no email address, outgoing mails keep their "
                "own sender and may be refused by the mail server", company.name,
            )
            continue
        local_part, domain_name = email.split('@', 1)

        personal_servers = IrMailServer.search([('owner_user_id', '!=', False)]).filtered(
            lambda server, mailbox=email: (
                server.from_filter and IrMailServer._match_from_filter(mailbox, server.from_filter)
            ) or email_normalize(server.smtp_user or '') == mailbox
        )
        if personal_servers:
            personal_servers.write({'owner_user_id': False})
            _logger.info(
                "sterrenboom: outgoing mail server(s) %s now serve the whole company instead "
                "of their owner only", ', '.join(personal_servers.mapped('name')),
            )

        alias_domain = company.alias_domain_id
        if alias_domain and alias_domain.name != domain_name:
            _logger.warning(
                "sterrenboom: company %s already uses alias domain %s, not %s: leaving "
                "its mail identity alone", company.name, alias_domain.name, domain_name,
            )
            continue
        if not alias_domain:
            alias_domain = AliasDomain.search([('name', '=', domain_name)], limit=1)
        try:
            if not alias_domain:
                alias_domain = AliasDomain.create({
                    'name': domain_name,
                    'default_from': local_part,
                    'catchall_alias': local_part,
                    'bounce_alias': local_part,
                })
                _logger.info(
                    "sterrenboom: created alias domain %s sending as %s", domain_name, email,
                )
            else:
                values = {}
                if email_normalize(alias_domain.default_from_email or '') != email:
                    values['default_from'] = local_part
                # only replace Odoo's defaults, not aliases the committee chose
                if alias_domain.catchall_alias == 'catchall':
                    values['catchall_alias'] = local_part
                if alias_domain.bounce_alias == 'bounce':
                    values['bounce_alias'] = local_part
                if values:
                    alias_domain.write(values)
        except (UserError, ValidationError) as error:
            # e.g. the alias clashes with an existing one; never block an upgrade or a
            # company edit over the mail configuration
            _logger.warning(
                "sterrenboom: could not configure the alias domain for %s: %s", email, error,
            )
            continue
        if company.alias_domain_id != alias_domain:
            company.alias_domain_id = alias_domain

        servers = env['ir.mail_server'].sudo().search([
            ('owner_user_id', '=', False),
            ('from_filter', '=', False),
        ])
        if servers:
            servers.write({'from_filter': email})
            _logger.info(
                "sterrenboom: outgoing mail server(s) %s now only send as %s",
                ', '.join(servers.mapped('name')), email,
            )


def post_init_hook(env):
    _apply_structured_communication(env)
    _apply_outgoing_mail_identity(env)
