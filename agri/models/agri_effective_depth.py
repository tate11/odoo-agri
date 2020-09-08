from odoo import api, fields, models


class AgriEffectiveDepth(models.Model):
    _name = 'agri.effectivedepth'
    _description = 'Effective Depth'

    name = fields.Char('Name', required=True)
