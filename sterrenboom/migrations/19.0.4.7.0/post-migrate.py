"""Re-apply the outgoing mail identity: personal servers for the mailbox are now shared.

See ``hooks._apply_outgoing_mail_identity``.
"""

from odoo import SUPERUSER_ID, api
from odoo.addons.sterrenboom.hooks import _apply_outgoing_mail_identity


def migrate(cr, version):
    if not version:
        return
    _apply_outgoing_mail_identity(api.Environment(cr, SUPERUSER_ID, {}))
