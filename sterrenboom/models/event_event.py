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
