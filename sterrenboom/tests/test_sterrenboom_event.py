from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSterrenboomEvent(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Event = cls.env['sterrenboom.event']
        cls.member = cls.env['sterrenboom.member'].create({
            'name': 'Event Attendee',
            'email': 'attendee@example.com',
        })

    def _make_event(self, **values):
        return self.Event.create({
            'name': 'Committee Meeting',
            'date': '2026-03-01 19:00:00',
            **values,
        })

    def test_default_state_is_planned(self):
        self.assertEqual(self._make_event().state, 'planned')

    def test_state_workflow_buttons(self):
        event = self._make_event()
        event.action_set_ongoing()
        self.assertEqual(event.state, 'ongoing')
        event.action_set_completed()
        self.assertEqual(event.state, 'completed')
        event.action_set_cancelled()
        self.assertEqual(event.state, 'cancelled')
        event.action_reset_to_planned()
        self.assertEqual(event.state, 'planned')

    def test_end_date_before_start_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_event(date_end='2026-02-28 19:00:00')

    def test_end_date_after_start_date_is_accepted(self):
        event = self._make_event(date_end='2026-03-01 21:00:00')
        self.assertTrue(event.date_end)

    def test_attendee_count_is_stored_and_recomputed(self):
        event = self._make_event(member_ids=[(4, self.member.id)])
        self.assertEqual(event.attendee_count, 1)
        event.member_ids = [(5, 0, 0)]
        self.assertEqual(event.attendee_count, 0)

    def test_state_is_not_copied_on_duplicate(self):
        event = self._make_event()
        event.action_set_completed()
        self.assertEqual(event.copy().state, 'planned')
