"""Put the Halloweentocht flyer header on the event record.

The event is ``noupdate`` data, so the new ``sterrenboom_header_image`` field stays
empty on existing databases; load the same JPEG the data file uses, unless the
committee already uploaded an image.
"""

import base64

from odoo import SUPERUSER_ID, api
from odoo.tools import file_open


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    event = env.ref('sterrenboom.event_halloweentocht_2026', raise_if_not_found=False)
    if not event or event.sterrenboom_header_image:
        return
    with file_open('sterrenboom/static/src/img/halloweentocht.jpg', 'rb', env=env) as image:
        event.sterrenboom_header_image = base64.b64encode(image.read())
