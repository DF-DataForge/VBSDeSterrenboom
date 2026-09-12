"""Apply the install-time configuration that existing databases missed.

``post_init_hook`` only runs when the module is installed, so an upgrade has to redo
the same work: sale journals still on Odoo's default communication standard get their
country's structured one, which is what the payment mail and the SEPA QR-code carry.

Migration scripts are not part of the addon package, so the hook cannot be imported
relatively here.
"""

from odoo import SUPERUSER_ID, api
from odoo.addons.sterrenboom.hooks import _apply_structured_communication


def migrate(cr, version):
    if not version:
        return
    _apply_structured_communication(api.Environment(cr, SUPERUSER_ID, {}))
