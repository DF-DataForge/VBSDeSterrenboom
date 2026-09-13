"""Send all outgoing mail from the company mailbox on existing databases.

``post_init_hook`` only runs at install, so the upgrade applies the same
configuration: an alias domain for the company email address and a FROM filter on
the outgoing mail servers. See ``hooks._apply_outgoing_mail_identity``.
"""

from odoo import SUPERUSER_ID, api
from odoo.addons.sterrenboom.hooks import _apply_outgoing_mail_identity


def migrate(cr, version):
    if not version:
        return
    _apply_outgoing_mail_identity(api.Environment(cr, SUPERUSER_ID, {}))
