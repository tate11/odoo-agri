from odoo import api, fields, models


class AgriEffectiveDepth(models.Model):
    _name = 'agri.effective.depth'
    _description = 'Effective Depth'

    name = fields.Char('Name', required=True)
