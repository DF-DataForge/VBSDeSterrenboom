from odoo.addons.sterrenboom.hooks import _apply_outgoing_mail_identity
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import email_normalize


@tagged('post_install', '-at_install')
class TestOutgoingMailIdentity(TransactionCase):
    """All outgoing mail leaves as the company mailbox, whoever the author is."""

    EMAIL = 'oc@sterrenboom-test.example'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.email = cls.EMAIL
        cls.company.alias_domain_id = False
        cls.server = cls.env['ir.mail_server'].create({
            'name': 'OC mailbox',
            'smtp_host': 'smtp.sterrenboom-test.example',
            'smtp_user': cls.EMAIL,
            'smtp_pass': 'secret',
        })
        cls.other_server = cls.env['ir.mail_server'].create({
            'name': 'Other provider',
            'smtp_host': 'smtp.other.example',
            'from_filter': 'other.example',
        })

    def test_company_mailbox_becomes_the_sender(self):
        _apply_outgoing_mail_identity(self.env)

        alias_domain = self.company.alias_domain_id
        self.assertEqual(alias_domain.name, 'sterrenboom-test.example')
        self.assertEqual(self.company.default_from_email, self.EMAIL)
        self.assertEqual(alias_domain.catchall_email, self.EMAIL)
        self.assertEqual(alias_domain.bounce_email, self.EMAIL)
        self.assertEqual(self.server.from_filter, self.EMAIL)
        # a server the committee configured for another domain is not touched
        self.assertEqual(self.other_server.from_filter, 'other.example')

    def test_odoobot_mail_goes_out_as_the_company(self):
        _apply_outgoing_mail_identity(self.env)
        servers = self.server | self.other_server

        server, smtp_from = self.env['ir.mail_server']._find_mail_server(
            '"OdooBot" <odoobot@example.com>', servers,
        )
        self.assertEqual(server, self.server)
        self.assertEqual(email_normalize(smtp_from), self.EMAIL)

        server, smtp_from = self.env['ir.mail_server']._find_mail_server(
            self.company.email_formatted, servers,
        )
        self.assertEqual(server, self.server)
        self.assertEqual(email_normalize(smtp_from), self.EMAIL)

    def test_running_twice_changes_nothing(self):
        _apply_outgoing_mail_identity(self.env)
        alias_domain = self.company.alias_domain_id
        count = self.env['mail.alias.domain'].search_count([])

        _apply_outgoing_mail_identity(self.env)

        self.assertEqual(self.company.alias_domain_id, alias_domain)
        self.assertEqual(self.env['mail.alias.domain'].search_count([]), count)
        self.assertEqual(self.server.from_filter, self.EMAIL)

    def test_hand_picked_aliases_are_kept(self):
        alias_domain = self.env['mail.alias.domain'].create({
            'name': 'sterrenboom-test.example',
            'catchall_alias': 'antwoorden',
        })
        self.company.alias_domain_id = alias_domain

        _apply_outgoing_mail_identity(self.env)

        self.assertEqual(alias_domain.default_from_email, self.EMAIL)
        self.assertEqual(alias_domain.catchall_alias, 'antwoorden')
        self.assertEqual(alias_domain.bounce_alias, 'oc')

    def test_another_alias_domain_is_respected(self):
        alias_domain = self.env['mail.alias.domain'].create({'name': 'other.example'})
        self.company.alias_domain_id = alias_domain

        _apply_outgoing_mail_identity(self.env)

        self.assertEqual(self.company.alias_domain_id, alias_domain)
        self.assertEqual(alias_domain.default_from, 'notifications')
        self.assertFalse(self.server.from_filter)

    def test_company_without_email_is_left_alone(self):
        self.company.email = False

        _apply_outgoing_mail_identity(self.env)

        self.assertFalse(self.company.alias_domain_id)
        self.assertFalse(self.server.from_filter)
