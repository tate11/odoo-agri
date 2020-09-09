from odoo import api, fields, models


class AgriSoilTexture(models.Model):
    _name = 'agri.soil.texture'
    _description = 'Soil Texture'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
