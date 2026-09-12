# models/sterrenboom_model.py
from odoo import models, fields


class SterrenboomMember(models.Model):
    """Parent committee member"""
    _name = 'sterrenboom.member'
    _description = 'Sterrenboom Committee Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    role = fields.Selection([
        ('chairman', 'Chairman'),
        ('treasurer', 'Treasurer'),
        ('secretary', 'Secretary'),
        ('member', 'Member'),
    ], string='Role', default='member')
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('unique_email', 'unique(email)', 'Email must be unique'),
    ]


class SterrenboomEvent(models.Model):
    """Parent committee events"""
    _name = 'sterrenboom.event'
    _description = 'Sterrenboom Committee Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Event Name', required=True)
    date = fields.Datetime(string='Event Date', required=True)
    location = fields.Char(string='Location')
    description = fields.Text(string='Description')
    member_ids = fields.Many2many('sterrenboom.member', string='Attendees')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='planned')
