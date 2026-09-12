from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SterrenboomEvent(models.Model):
    """Event organised by the VBS De Sterrenboom parent committee."""

    _name = 'sterrenboom.event'
    _description = 'Sterrenboom Committee Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Event Name', required=True, tracking=True)
    date = fields.Datetime(string='Start', required=True, tracking=True)
    date_end = fields.Datetime(string='End', tracking=True)
    location = fields.Char(string='Location')
    description = fields.Html(string='Description')
    notes = fields.Html(string='Internal Notes')
    active = fields.Boolean(string='Active', default=True)
    member_ids = fields.Many2many(
        comodel_name='sterrenboom.member',
        relation='sterrenboom_event_member_rel',
        column1='event_id',
        column2='member_id',
        string='Attendees',
    )
    attendee_count = fields.Integer(
        string='Attendees',
        compute='_compute_attendee_count',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('planned', 'Planned'),
            ('ongoing', 'Ongoing'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='planned',
        required=True,
        tracking=True,
        copy=False,
    )

    @api.depends('member_ids')
    def _compute_attendee_count(self):
        for event in self:
            event.attendee_count = len(event.member_ids)

    @api.constrains('date', 'date_end')
    def _check_dates(self):
        for event in self:
            if event.date_end and event.date_end < event.date:
                raise ValidationError(
                    _("The end date of '%s' cannot be before its start date.", event.name)
                )

    def action_set_ongoing(self):
        self.write({'state': 'ongoing'})

    def action_set_completed(self):
        self.write({'state': 'completed'})

    def action_set_cancelled(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_planned(self):
        self.write({'state': 'planned'})
