from odoo import api, fields, models


class AgriEffectiveDepth(models.Model):
    _name = 'agri.effectivedepth'
    _description = 'Effective Depths'

    name = fields.Char('Name', required=True)
