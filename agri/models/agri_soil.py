from odoo import api, fields, models


class SoilEffectiveDepth(models.Model):
    _name = 'agri.soil.effective.depth'
    _description = 'Effective Depth'

    name = fields.Char('Name', required=True)


class SoilTexture(models.Model):
    _name = 'agri.soil.texture'
    _description = 'Soil Texture'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
