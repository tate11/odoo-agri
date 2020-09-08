from odoo import api, fields, models


class AgriSoilTexture(models.Model):
    _name = 'agri.soiltexture'
    _description = 'Soil Texture'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
