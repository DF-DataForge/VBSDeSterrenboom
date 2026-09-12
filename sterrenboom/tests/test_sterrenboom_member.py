from psycopg2 import IntegrityError

from odoo.fields import Command
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestSterrenboomMember(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Member = cls.env['sterrenboom.member']

    def test_default_role_is_member(self):
        member = self.Member.create({'name': 'Test Member'})
        self.assertEqual(member.role, 'member')
        self.assertTrue(member.active)

    def test_email_must_be_unique(self):
        self.Member.create({'name': 'First', 'email': 'dup@example.com'})
        with (
            self.assertRaises(IntegrityError),
            mute_logger('odoo.sql_db'),
            self.env.cr.savepoint(),
        ):
            self.Member.create({'name': 'Second', 'email': 'dup@example.com'})
            self.env.flush_all()

    def test_members_without_email_are_allowed(self):
        """A NULL email must not collide with the unique constraint."""
        self.Member.create({'name': 'No Email One'})
        self.Member.create({'name': 'No Email Two'})
        self.env.flush_all()

    def test_event_count_tracks_linked_events(self):
        member = self.Member.create({'name': 'Counted Member'})
        self.assertEqual(member.event_count, 0)
        self.env['sterrenboom.event'].create({
            'name': 'Linked Event',
            'date': '2026-01-01 19:00:00',
            'member_ids': [Command.link(member.id)],
        })
        self.assertEqual(member.event_count, 1)

    def test_archiving_hides_member_from_default_search(self):
        member = self.Member.create({'name': 'To Archive'})
        member.active = False
        self.assertNotIn(member, self.Member.search([('name', '=', 'To Archive')]))
        self.assertIn(
            member,
            self.Member.with_context(active_test=False).search([('name', '=', 'To Archive')]),
        )
