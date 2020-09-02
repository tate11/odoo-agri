from odoo import api, fields, models


class AgriWaterSource(models.Model):
    _name = 'agri.watersource'
    _description = 'Water Sources'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
