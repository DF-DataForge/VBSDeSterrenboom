"""Reload both mail templates: they no longer use Odoo's "Default Recipients".

With that option on, Odoo added the customer as a partner recipient next to the
addresses in email_to and delivered the tickets mail (and the payment mail) twice.
See migrations/19.0.4.0.0/post-migrate.py for why a noupdate record needs this.
"""

from odoo import SUPERUSER_ID, api
from odoo.tools.convert import convert_file


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    convert_file(env, 'sterrenboom', 'data/mail_template_data.xml', None, mode='init')
