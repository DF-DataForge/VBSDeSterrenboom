from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPoweredByDataForge(TransactionCase):
    """'powered by Data Forge' with logo and link on mails and tickets."""

    def test_outgoing_mail_gets_the_footer(self):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Dag Piet,</p>',
            'email_to': 'piet@example.com',
        })

        body = mail._prepare_outgoing_body()

        self.assertIn('<p>Dag Piet,</p>', body)
        self.assertIn('href="https://www.data-forge.be"', body)
        self.assertIn('/sterrenboom/static/src/img/dataforge_logo.png', body)
        self.assertIn('powered by', body)
        # the logo URL is absolute, mail clients cannot resolve a relative one
        self.assertIn(mail.get_base_url() + '/sterrenboom/static/src/img/dataforge_logo.png', body)

    def test_empty_mail_stays_empty(self):
        mail = self.env['mail.mail'].create({'subject': 'Empty', 'email_to': 'piet@example.com'})

        self.assertEqual(mail._prepare_outgoing_body(), '')

    def _ticket_html(self, event_values=None):
        event = self.env['event.event'].create({
            'name': 'Testtocht',
            'date_begin': '2030-10-23 16:30:00',
            'date_end': '2030-10-23 21:00:00',
            **(event_values or {}),
        })
        registration = self.env['event.registration'].create({
            'event_id': event.id,
            'name': 'Piet Van Haute',
            'email': 'piet@example.com',
        })
        html, _report_type = self.env['ir.actions.report']._render_qweb_html(
            'event.action_report_event_registration_full_page_ticket', registration.ids,
        )
        return html.decode()

    def test_ticket_carries_the_footer(self):
        html = self._ticket_html()

        self.assertIn('href="https://www.data-forge.be"', html)
        self.assertIn('/sterrenboom/static/src/img/dataforge_logo.png', html)

    def test_ticket_shows_attendee_and_event(self):
        html = self._ticket_html()

        self.assertIn('o_sb_ticket_card', html)
        self.assertIn('Piet Van Haute', html)
        self.assertIn('Testtocht', html)
        self.assertIn('Toon deze code aan de inkom', html)
        # no artwork: the banner carries the event name instead
        self.assertIn('o_sb_ticket_banner_text', html)

    def test_ticket_has_a_qr_code_but_no_barcode(self):
        self.env['ir.config_parameter'].sudo().set_param('event.use_event_barcode', 'True')

        html = self._ticket_html()

        self.assertIn('/report/barcode/QR/', html)
        self.assertNotIn('barcode_type=Code128', html)

    def test_ticket_banner_uses_the_header_image(self):
        halloween = self.env.ref('sterrenboom.event_halloweentocht_2026')
        self.assertTrue(halloween.sterrenboom_header_image, "data file did not load the artwork")

        html = self._ticket_html({'sterrenboom_header_image': halloween.sterrenboom_header_image})

        self.assertIn('background-image: url(data:image/', html)
        self.assertNotIn('o_sb_ticket_banner_text', html)
