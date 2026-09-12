"""Move ticket prices onto the standard ``event.event.ticket.price`` field.

19.0.3.0.0 drops ``sterrenboom_price``: the registration flow now produces a real sales
order and invoice, so the price has to live on the field ``event_sale`` prices its order
lines from. Runs before the field is removed, while its column still exists.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT column_name
          FROM information_schema.columns
         WHERE table_name = 'event_event_ticket'
           AND column_name IN ('sterrenboom_price', 'price')
    """)
    columns = {row[0] for row in cr.fetchall()}
    if columns != {'sterrenboom_price', 'price'}:
        return
    cr.execute("""
        UPDATE event_event_ticket
           SET price = sterrenboom_price
         WHERE sterrenboom_price IS NOT NULL
           AND sterrenboom_price > 0
           AND COALESCE(price, 0) = 0
    """)
    _logger.info("sterrenboom: copied sterrenboom_price to price on %s tickets", cr.rowcount)
