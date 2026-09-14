from odoo import models

from ..hooks import _apply_outgoing_mail_identity


class ResCompany(models.Model):
    """Re-apply the outgoing mail identity when the company email address is set."""

    _inherit = 'res.company'

    def write(self, vals):
        result = super().write(vals)
        if vals.get('email') and not self.env.context.get('sterrenboom_skip_mail_identity'):
            _apply_outgoing_mail_identity(self.env)
        return result
