from odoo import http
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.http import request


class SterrenboomWebsiteEventController(WebsiteEventController):

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
        return request.render(view_sudo.key or view_sudo.id, values)
