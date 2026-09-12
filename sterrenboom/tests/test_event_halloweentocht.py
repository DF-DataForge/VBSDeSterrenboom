from datetime import datetime

from psycopg2.errors import CheckViolation

from odoo.tests.common import HttpCase, TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestHalloweentochtData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env.ref('sterrenboom.event_halloweentocht_2026')
        cls.page_view = cls.env.ref('sterrenboom.event_page_halloweentocht')

    def test_event_matches_flyer(self):
        self.assertEqual(self.event.name, 'Halloweentocht')
        self.assertEqual(self.event.date_tz, 'Europe/Brussels')
        # 23/10/2026 18:30 Europe/Brussels (CEST) stored as UTC
        self.assertEqual(self.event.date_begin, datetime(2026, 10, 23, 16, 30))
        self.assertLess(self.event.date_begin, self.event.date_end)
        self.assertEqual(self.event.address_id.name, 'Kerk van Wortegem')
        self.assertFalse(self.event.seats_limited)

    def test_event_is_published_with_custom_page(self):
        self.assertTrue(self.event.website_published)
        self.assertEqual(self.event.sterrenboom_page_view_id, self.page_view)
        self.assertEqual(self.page_view.type, 'qweb')

    def test_tickets_match_flyer(self):
        tickets = self.event.event_ticket_ids.sorted('sequence')
        self.assertEqual(tickets.mapped('name'), ['Volwassene', 'Kind'])
        self.assertEqual(tickets.mapped('sterrenboom_price'), [12.0, 10.0])
        for ticket in tickets:
            # Registrations close before 17/10/2026 (23:59:59 Europe/Brussels)
            self.assertEqual(ticket.end_sale_datetime, datetime(2026, 10, 16, 21, 59, 59))
            self.assertFalse(ticket.seats_limited)

    @mute_logger('odoo.sql_db')
    def test_negative_ticket_price_is_rejected(self):
        with self.assertRaises(CheckViolation), self.env.cr.savepoint():
            self.env['event.event.ticket'].create({
                'event_id': self.event.id,
                'name': 'Negative',
                'sterrenboom_price': -1.0,
            })
            self.env.flush_all()


@tagged('post_install', '-at_install')
class TestHalloweentochtPage(HttpCase):

    def test_event_url_opens_custom_page(self):
        event = self.env.ref('sterrenboom.event_halloweentocht_2026')
        response = self.url_open(f'/event/{event.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_sterrenboom_halloween', response.text)
        self.assertIn('Trick or Treat', response.text)
        self.assertIn('Gratis drankje bij verkleding', response.text)
        # registration modal from website_event.layout is present on the custom page
        self.assertIn('id="modal_ticket_registration"', response.text)

    def test_event_without_custom_page_keeps_standard_page(self):
        event = self.env['event.event'].create({
            'name': 'Standaard evenement',
            'date_begin': '2030-01-01 18:00:00',
            'date_end': '2030-01-01 20:00:00',
            'website_published': True,
        })
        response = self.url_open(f'/event/{event.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('o_sterrenboom_halloween', response.text)
        self.assertIn('o_wevent_event_main', response.text)
