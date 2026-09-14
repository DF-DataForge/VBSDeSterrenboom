from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon
from odoo.tests.common import tagged


@tagged('post_install', '-at_install')
class TestPaymentQrRoute(AccountTestInvoicingHttpCommon):
    """The SEPA QR-code the payment mail embeds is served by a token-guarded route."""

    country_code = 'BE'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref('account.group_validate_bank_account')
        company = cls.env.company
        cls.env['res.partner.bank'].create({
            'acc_number': 'BE15001559627230',
            'partner_id': company.partner_id.id,
            'company_id': company.id,
            'allow_out_payment': True,
        })
        cls.invoice = cls.init_invoice('out_invoice', amounts=[12.0], post=True)

    def test_qr_code_is_served_with_the_token(self):
        url = self.invoice._sterrenboom_payment_qr_url()
        self.assertTrue(url)

        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG'))

    def test_qr_code_needs_the_right_token(self):
        self.invoice._sterrenboom_payment_qr_url()

        self.assertEqual(
            self.url_open(f'/sterrenboom/payment_qr/{self.invoice.id}').status_code, 404,
        )
        self.assertEqual(
            self.url_open(f'/sterrenboom/payment_qr/{self.invoice.id}?access_token=wrong').status_code,
            404,
        )
