from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.account.tools import is_valid_structured_reference
from odoo.exceptions import UserError
from odoo.tests.common import tagged


@tagged('post_install', '-at_install')
class TestRegistrationPayment(AccountTestInvoicingCommon):
    """The website registration flow: sales order -> posted invoice -> payment details.

    Runs on a Belgian company with the Belgian chart, which is what the committee uses:
    that is what gives the sale journal the "+++000/0000/00000+++" communication standard
    and the euro currency the SEPA QR-code needs.
    """

    country_code = 'BE'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The accounting test user has neither Events nor Sales rights, but the website
        # flow creates events, registrations and sales orders with them.
        cls.env.user.group_ids |= (
            cls.env.ref('event.group_event_manager')
            | cls.env.ref('sales_team.group_sale_salesman')
            | cls.env.ref('account.group_validate_bank_account')
        )
        company = cls.env.company
        cls.bank = cls.env['res.partner.bank'].create({
            'acc_number': 'BE15001559627230',
            'partner_id': company.partner_id.id,
            'company_id': company.id,
            # account refuses to post an invoice carrying an untrusted company account.
            'allow_out_payment': True,
        })
        cls.ticket_product = cls.env['product.product'].create({
            'name': 'Inschrijving evenement',
            'type': 'service',
            'service_tracking': 'event',
            'invoice_policy': 'order',
            'list_price': 0.0,
            'taxes_id': [Command.clear()],
            'property_account_income_id': cls.company_data['default_account_revenue'].id,
        })
        cls.event = cls.env['event.event'].create({
            'name': 'Testtocht',
            'date_begin': '2030-10-23 16:30:00',
            'date_end': '2030-10-23 21:00:00',
            'date_tz': 'Europe/Brussels',
            'website_published': True,
            'event_ticket_ids': [
                Command.create({
                    'name': 'Volwassene',
                    'product_id': cls.ticket_product.id,
                    'price': 12.0,
                }),
                Command.create({
                    'name': 'Kind',
                    'product_id': cls.ticket_product.id,
                    'price': 10.0,
                }),
            ],
        })
        cls.attendee_partner = cls.env['res.partner'].create({
            'name': 'Piet Van Haute',
            'email': 'piet@example.com',
        })

    def _book(self, tickets=None):
        """Mimic what website_event_sale builds from the attendee form: an order with
        one line per ticket type and one registration per attendee."""
        tickets = tickets if tickets is not None else self.event.event_ticket_ids
        order = self.env['sale.order'].create({
            'partner_id': self.attendee_partner.id,
            'order_line': [
                Command.create({
                    'product_id': ticket.product_id.id,
                    'event_id': self.event.id,
                    'event_ticket_id': ticket.id,
                    'product_uom_qty': 1,
                })
                for ticket in tickets
            ],
        })
        registrations = self.env['event.registration'].create([
            {
                'sale_order_line_id': line.id,
                'name': 'Piet Van Haute' if index == 0 else 'Mila Van Haute',
                'email': 'piet@example.com' if index == 0 else 'mila@example.com',
            }
            for index, line in enumerate(order.order_line)
        ])
        return order, registrations

    def _ticket_mails(self, registrations):
        """Outgoing mails addressed to these attendees (the confirmation with the ticket)."""
        return self.env['mail.mail'].search([
            ('model', '=', 'event.registration'),
            ('res_id', 'in', registrations.ids),
        ])

    def test_order_is_confirmed_and_invoiced(self):
        order, registrations = self._book()

        invoice = order._sterrenboom_invoice_registrations()

        self.assertEqual(order.state, 'sale')
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(invoice.partner_id, self.attendee_partner)
        self.assertAlmostEqual(invoice.amount_total, 22.0)
        self.assertEqual(registrations._sterrenboom_invoice(), invoice)

    def test_invoicing_twice_reuses_the_same_invoice(self):
        order, _registrations = self._book()

        first = order._sterrenboom_invoice_registrations()
        second = order._sterrenboom_invoice_registrations()

        self.assertEqual(first, second)
        self.assertEqual(len(order.invoice_ids), 1)

    def test_free_registration_is_not_invoiced(self):
        self.event.event_ticket_ids.price = 0.0
        order, registrations = self._book()

        self.assertFalse(order._sterrenboom_invoice_registrations())
        self.assertFalse(registrations._sterrenboom_payment_values())

    def test_payment_reference_is_a_structured_communication(self):
        order, registrations = self._book()
        invoice = order._sterrenboom_invoice_registrations()

        values = registrations._sterrenboom_payment_values()

        self.assertEqual(values['communication'], invoice.payment_reference)
        self.assertTrue(
            is_valid_structured_reference(values['communication']),
            f"{values['communication']!r} is not a structured communication; check the "
            "'Communication Standard' of the sale journal",
        )

    def test_confirmation_page_gets_a_sepa_qr_code(self):
        order, registrations = self._book()
        invoice = order._sterrenboom_invoice_registrations()

        values = registrations._sterrenboom_payment_values()

        self.assertEqual(values['bank'], self.bank)
        self.assertAlmostEqual(values['amount'], invoice.amount_residual)
        self.assertTrue(values['qr_code'].startswith('data:image/png;base64,'))

    def test_payment_instructions_mail_carries_the_communication(self):
        order, registrations = self._book()
        invoice = order._sterrenboom_invoice_registrations()

        mails = registrations._sterrenboom_send_payment_instructions(force_send=False)

        self.assertEqual(len(mails), 1)
        self.assertIn('piet@example.com', mails.email_to)
        self.assertIn('mila@example.com', mails.email_to)
        self.assertIn(invoice.payment_reference, mails.body_html)
        self.assertIn(self.bank.acc_number, mails.body_html)
        self.assertIn('Testtocht', mails.body_html)

    def test_invoiced_attendees_wait_for_the_payment(self):
        order, registrations = self._book()

        order._sterrenboom_invoice_registrations()

        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.sterrenboom_tickets_on_hold)
        self.assertFalse(order.sterrenboom_tickets_sent_date)
        # confirming the order would normally register the attendees and mail the tickets
        self.assertEqual(set(registrations.mapped('state')), {'draft'})
        self.assertEqual(set(registrations.mapped('sale_status')), {'to_pay'})
        self.assertFalse(registrations.mail_registration_ids.filtered('mail_sent'))
        self.assertFalse(self._ticket_mails(registrations))

    def _tickets_mails(self, order):
        """The tickets mails of an order (one per click on Send Tickets)."""
        return self.env['mail.mail'].search([
            ('model', '=', 'sale.order'),
            ('res_id', '=', order.id),
        ])

    def test_send_tickets_registers_the_attendees_and_mails_one_mail(self):
        order, registrations = self._book()
        order._sterrenboom_invoice_registrations()

        action = order.action_sterrenboom_send_tickets()

        self.assertFalse(order.sterrenboom_tickets_on_hold)
        self.assertTrue(order.sterrenboom_tickets_sent_date)
        self.assertEqual(set(registrations.mapped('state')), {'open'})
        self.assertEqual(set(registrations.mapped('sale_status')), {'sold'})
        # one mail to the customer with a ticket per attendee attached
        mails = self._tickets_mails(order)
        self.assertEqual(len(mails), 1)
        self.assertIn('piet@example.com', mails.email_to)
        self.assertIn('Testtocht', mails.subject)
        self.assertIn('Mila Van Haute', mails.body_html)
        self.assertEqual(len(mails.attachment_ids), 2)
        self.assertTrue(all(name.endswith('.pdf') for name in mails.attachment_ids.mapped('name')))
        # Odoo's per-attendee confirmation mail was neither sent nor left for the cron
        self.assertFalse(self._ticket_mails(registrations))
        self.assertEqual(len(registrations.mail_registration_ids.filtered('mail_sent')), 2)
        # delivered on the spot and reported in a popup
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')
        self.assertIn('2 attendee(s)', action['params']['message'])
        self.assertIn('piet@example.com', action['params']['message'])

    def test_send_tickets_without_event_communication(self):
        self.event.event_mail_ids.unlink()
        order, registrations = self._book()
        order._sterrenboom_invoice_registrations()

        action = order.action_sterrenboom_send_tickets()

        self.assertEqual(set(registrations.mapped('state')), {'open'})
        mails = self._tickets_mails(order)
        self.assertEqual(len(mails), 1)
        self.assertEqual(len(mails.attachment_ids), 2)
        self.assertEqual(action['params']['type'], 'success')

    def test_send_tickets_again_resends_them(self):
        order, registrations = self._book()
        order._sterrenboom_invoice_registrations()
        order.action_sterrenboom_send_tickets()

        action = order.action_sterrenboom_send_tickets()

        self.assertEqual(set(registrations.mapped('state')), {'open'})
        self.assertEqual(len(self._tickets_mails(order)), 2)
        self.assertEqual(action['params']['type'], 'success')
        self.assertFalse(self._ticket_mails(registrations))

    def test_send_tickets_needs_a_confirmed_order(self):
        order, _registrations = self._book()

        with self.assertRaises(UserError):
            order.action_sterrenboom_send_tickets()

    def test_payment_instructions_mail_says_the_tickets_follow(self):
        order, registrations = self._book()
        order._sterrenboom_invoice_registrations()

        mails = registrations._sterrenboom_send_payment_instructions(force_send=False)

        self.assertIn('Hieronder vind je de gegevens voor de overschrijving.', mails.body_html)
        self.assertIn('mag je deze mail negeren', mails.body_html)
        self.assertIn(
            'De tickets worden doorgestuurd zodra jouw betaling verwerkt is.', mails.body_html
        )
        self.assertNotIn('niet via de website', mails.body_html)
        # no reference to the invoice: attendees only see the transfer details
        self.assertNotIn('factuur', mails.body_html)
        self.assertNotIn(order.invoice_ids.name, mails.body_html)
