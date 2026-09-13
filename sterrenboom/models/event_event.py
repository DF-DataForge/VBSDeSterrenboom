from odoo import fields, models


class EventEvent(models.Model):
    """Let an Odoo Events record point at its own website page template."""

    _inherit = 'event.event'

    sterrenboom_page_view_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Custom Website Page',
        domain="[('type', '=', 'qweb')]",
        ondelete='set null',
        help="QWeb template rendered instead of the standard event page when a visitor "
             "opens this event on the website. Leave empty to keep the standard page.",
    )
    sterrenboom_header_image = fields.Image(
        string='Header Image',
        max_width=1920,
        max_height=1920,
        help="Artwork shown across the top of the event's custom website page and of "
             "its tickets. A wide banner (about 2:1) works best.",
    )
