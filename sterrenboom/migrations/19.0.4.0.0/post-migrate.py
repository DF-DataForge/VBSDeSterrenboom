"""Refresh the payment-instructions mail template on existing databases.

``data/mail_template_data.xml`` is ``noupdate``: Odoo creates the template once and then
leaves it alone so the committee can edit it in the UI. 19.0.4.0.0 changes its text (the
tickets now follow once the payment is processed), so the file is reloaded in ``init``
mode, which rewrites noupdate records. Edits made to the template in the UI are lost.
"""

from odoo import SUPERUSER_ID, api
from odoo.tools.convert import convert_file


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    convert_file(env, 'sterrenboom', 'data/mail_template_data.xml', None, mode='init')
