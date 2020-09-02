from odoo import api, fields, models


class AgriTerrain(models.Model):
    _name = 'agri.terrain'
    _description = 'Terrains'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
