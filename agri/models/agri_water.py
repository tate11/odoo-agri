from odoo import api, fields, models


class WaterSource(models.Model):
    _name = 'agri.water.source'
    _description = 'Water Source'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
