from datetime import datetime

from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestChurchOfSinnersData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env.ref('sterrenboom.event_church_of_sinners_2026')
        cls.page_view = cls.env.ref('sterrenboom.event_page_church_of_sinners')

    def test_event_matches_poster(self):
        self.assertEqual(self.event.name, 'Church of Sinners')
        self.assertEqual(self.event.date_tz, 'Europe/Brussels')
        # 23/10/2026 20:00 - 24/10/2026 02:00 Europe/Brussels (CEST) stored as UTC
        self.assertEqual(self.event.date_begin, datetime(2026, 10, 23, 18, 0))
        self.assertEqual(self.event.date_end, datetime(2026, 10, 24, 0, 0))
        self.assertFalse(self.event.seats_limited)
        self.assertTrue(self.event.sterrenboom_header_image, "data file did not load the artwork")

    def test_same_evening_and_venue_as_halloweentocht(self):
        halloween = self.env.ref('sterrenboom.event_halloweentocht_2026')
        self.assertEqual(self.event.date_begin.date(), halloween.date_begin.date())
        self.assertEqual(self.event.address_id, halloween.address_id)
        self.assertEqual(self.event.address_id.name, 'Kerk van Wortegem')

    def test_event_is_published_with_custom_page(self):
        self.assertTrue(self.event.website_published)
        self.assertEqual(self.event.sterrenboom_page_view_id, self.page_view)
        self.assertEqual(self.page_view.type, 'qweb')

    def test_only_an_adult_ticket(self):
        tickets = self.event.event_ticket_ids
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket.name, 'Volwassene')
        self.assertEqual(ticket.price, 8.0)
        # Registrations close when the doors open (23/10/2026 20:00 Europe/Brussels)
        self.assertEqual(ticket.end_sale_datetime, self.event.date_begin)
        self.assertFalse(ticket.seats_limited)
        # event_sale prices its order lines from the ticket's product, which is what
        # makes the registration go through the sales order -> invoice -> payment flow.
        self.assertTrue(ticket.product_id)


@tagged('post_install', '-at_install')
class TestChurchOfSinnersPage(HttpCase):

    def test_event_url_opens_custom_page(self):
        event = self.env.ref('sterrenboom.event_church_of_sinners_2026')
        response = self.url_open(f'/event/{event.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_sterrenboom_church', response.text)
        self.assertNotIn('o_sterrenboom_halloween', response.text)
        self.assertIn('DJ Brightside', response.text)
        self.assertIn('DJ Ira Mira', response.text)
        self.assertIn('Enkel voor volwassenen', response.text)
        # registration modal from website_event.layout is present on the custom page
        self.assertIn('id="modal_ticket_registration"', response.text)
        # the header artwork comes from the event record, shared with the tickets
        self.assertIn(f'/web/image/event.event/{event.id}/sterrenboom_header_image', response.text)
        self.assertIn('/sterrenboom/static/src/img/church_of_sinners_poster.jpg', response.text)
        # powered by Data Forge, logo linking to their website
        self.assertIn('href="https://www.data-forge.be"', response.text)
        self.assertIn('/sterrenboom/static/src/img/dataforge_logo.png', response.text)

    def test_no_halloweentocht_fallback_header_without_artwork(self):
        event = self.env.ref('sterrenboom.event_church_of_sinners_2026')
        event.sterrenboom_header_image = False
        response = self.url_open(f'/event/{event.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('/sterrenboom/static/src/img/halloweentocht.jpg', response.text)
        self.assertIn('o_sb_title', response.text)
