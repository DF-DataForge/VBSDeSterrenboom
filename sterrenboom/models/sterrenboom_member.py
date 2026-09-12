from odoo import api, fields, models


class SterrenboomMember(models.Model):
    """Member of the VBS De Sterrenboom parent committee."""

    _name = 'sterrenboom.member'
    _description = 'Sterrenboom Committee Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    email = fields.Char(tracking=True)
    phone = fields.Char()
    role = fields.Selection(
        selection=[
            ('chairman', 'Chairman'),
            ('treasurer', 'Treasurer'),
            ('secretary', 'Secretary'),
            ('member', 'Member'),
        ],
        default='member',
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    event_ids = fields.Many2many(
        comodel_name='sterrenboom.event',
        relation='sterrenboom_event_member_rel',
        column1='member_id',
        column2='event_id',
        string='Events',
    )
    event_count = fields.Integer(compute='_compute_event_count')

    _unique_email = models.Constraint(
        'unique (email)',
        "A committee member with this email address already exists.",
    )

    @api.depends('event_ids')
    def _compute_event_count(self):
        for member in self:
            member.event_count = len(member.event_ids)
