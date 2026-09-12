from odoo import fields, models


class EventEventTicket(models.Model):
    """Show a ticket price on the website without installing eCommerce."""

    _inherit = 'event.event.ticket'

    sterrenboom_price = fields.Float(
        string='Price (€)',
        digits=(16, 2),
        help="Price per person shown on the website. Payment is collected by the "
             "committee, not through the website.",
    )

    _sterrenboom_price_positive = models.Constraint(
        'CHECK (sterrenboom_price >= 0)',
        "A ticket price cannot be negative.",
    )
