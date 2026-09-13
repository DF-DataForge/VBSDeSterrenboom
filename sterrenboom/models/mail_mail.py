from markupsafe import Markup

from odoo import models

DATA_FORGE_URL = 'https://www.data-forge.be'
DATA_FORGE_LOGO = '/sterrenboom/static/src/img/dataforge_logo.png'


class MailMail(models.Model):
    """Sign every outgoing mail with 'powered by Data Forge'."""

    _inherit = 'mail.mail'

    def _prepare_outgoing_body(self):
        body = super()._prepare_outgoing_body()
        if not body:
            return body
        return Markup(body) + self._sterrenboom_powered_by_footer()

    def _sterrenboom_powered_by_footer(self):
        """Centered footer with the Data Forge logo linking to its website.

        Inline styles and an absolute image URL, as mail clients need them.
        """
        base_url = self.get_base_url()
        return Markup(
            '<div style="margin-top: 24px; padding-top: 12px; border-top: 1px solid #e5e5e5; '
            'text-align: center; font-size: 12px; color: #888888;">'
            '<a href="{url}" target="_blank" '
            'style="color: #888888; text-decoration: none;">powered by '
            '<img src="{base_url}{logo}" alt="Data Forge" height="22" '
            'style="height: 22px; vertical-align: middle;"/></a>'
            '</div>'
        ).format(url=DATA_FORGE_URL, base_url=base_url, logo=DATA_FORGE_LOGO)
