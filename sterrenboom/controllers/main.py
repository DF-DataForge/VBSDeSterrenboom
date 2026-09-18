from werkzeug.exceptions import NotFound
from werkzeug.urls import url_encode

from odoo import http
from odoo.addons.website_event_sale.controllers.main import WebsiteEventSaleController
from odoo.http import request
from odoo.tools import consteq
from odoo.tools.misc import file_path

# Registrations created by the request currently being processed, handed from
# _create_attendees_from_registration_post() to registration_confirm().
SESSION_KEY = 'sterrenboom_registration_ids'

# Fallback flyer header for the Halloweentocht page when the event record carries no
# Header Image: a web-sized JPEG of "Header halloweentocht.png" from the repository root.
HEADER_IMAGE = 'sterrenboom/static/src/img/halloweentocht.jpg'
HEADER_IMAGE_PAGE = 'sterrenboom.event_page_halloweentocht'


class SterrenboomWebsiteEventController(WebsiteEventSaleController):

    @http.route()
    def event_register(self, event, **post):
        """Serve the event's custom website page when one is configured.

        ``/event/<slug>`` redirects here, so setting *Custom Website Page* on an
        event replaces the standard Odoo event page for visitors. The registration
        modal is still provided by ``website_event.layout``, so the standard ticket
        selection and attendee flow keep working from the custom page.
        """
        view_sudo = event.sudo().sterrenboom_page_view_id
        if not view_sudo:
            return super().event_register(event, **post)
        values = self._prepare_event_register_values(event, **post)
        values['sterrenboom_header_image'] = self._sterrenboom_header_image_url(event)
        return request.render(view_sudo.key or view_sudo.id, values)

    def _sterrenboom_header_image_url(self, event):
        """URL of the event's header artwork, or ``False`` when there is none.

        The Header Image on the event record wins (the tickets use the same one); the
        static Halloweentocht flyer is the fallback, for the Halloweentocht page only:
        other events (Church of Sinners) show their typographic title instead.
        """
        event_sudo = event.sudo()
        if event_sudo.sterrenboom_header_image:
            return (
                f'/web/image/event.event/{event.id}/sterrenboom_header_image'
                f'?unique={event_sudo.write_date.timestamp():.0f}'
            )
        if event_sudo.sterrenboom_page_view_id.key != HEADER_IMAGE_PAGE:
            return False
        try:
            file_path(HEADER_IMAGE, filter_ext=('.jpg', '.jpeg', '.png'))
        except (FileNotFoundError, ValueError):
            return False
        return f'/{HEADER_IMAGE}'

    @http.route(['/sterrenboom/payment_qr/<int:invoice_id>'], type='http', auth='public',
                methods=['GET'], website=True, sitemap=False)
    def payment_qr(self, invoice_id, access_token=None, **kwargs):
        """The SEPA QR-code of an invoice as PNG, for the payment-instructions mail.

        Guarded by the invoice's portal access token: whoever received the mail holds
        it, nobody else can enumerate invoices.
        """
        invoice_sudo = request.env['account.move'].sudo().browse(invoice_id).exists()
        if (
            not invoice_sudo or not access_token or not invoice_sudo.access_token
            or not consteq(invoice_sudo.access_token, access_token)
        ):
            raise NotFound()
        png = invoice_sudo._sterrenboom_payment_qr_png()
        if not png:
            raise NotFound()
        return request.make_response(png, headers=[
            ('Content-Type', 'image/png'),
            ('Content-Length', str(len(png))),
            ('Cache-Control', 'private, max-age=3600'),
        ])

    def _create_attendees_from_registration_post(self, event, registration_data):
        """Remember what was booked so registration_confirm() can invoice it."""
        attendees_sudo = super()._create_attendees_from_registration_post(event, registration_data)
        request.session[SESSION_KEY] = attendees_sudo.ids
        return attendees_sudo

    @http.route()
    def registration_confirm(self, event, **post):
        """Invoice the registration and show the confirmation page straight away.

        ``website_event_sale`` sends the visitor to the eCommerce checkout to pay
        online. The committee is paid by bank transfer instead, so the sales order is
        confirmed and invoiced here, the attendee is mailed the payment instructions,
        and the visitor lands on the standard confirmation page -- which
        ``sterrenboom.registration_complete_payment`` extends with the amount, the
        structured communication and a scannable SEPA QR-code.
        """
        # Never act on what a previous, aborted request may have left behind.
        request.session.pop(SESSION_KEY, None)
        response = super().registration_confirm(event, **post)
        registration_ids = request.session.pop(SESSION_KEY, None)
        if not registration_ids:
            # Seat check, reCaptcha or ticket validation refused the registration.
            return response

        attendees_sudo = request.env['event.registration'].sudo().browse(registration_ids).exists()
        if not attendees_sudo:
            return response

        orders_sudo = attendees_sudo.sale_order_id
        for order_sudo in orders_sudo:
            order_sudo._sterrenboom_invoice_registrations()
        if orders_sudo:
            # The order is paid offline from here on: start the next visitor's
            # registration from an empty cart.
            request.website.sale_reset()
        attendees_sudo._sterrenboom_send_payment_instructions()

        query = url_encode({
            'registration_ids': ','.join(str(rid) for rid in attendees_sudo.ids),
        })
        return request.redirect(f'/event/{event.id}/registration/success?{query}')

    def _get_registration_confirm_values(self, event, attendees_sudo):
        """Add the bank transfer details to the confirmation page."""
        values = super()._get_registration_confirm_values(event, attendees_sudo)
        values['sterrenboom_payment'] = attendees_sudo._sterrenboom_payment_values()
        return values
