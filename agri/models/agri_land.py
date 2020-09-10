from odoo import api, fields, models


class LandUse(models.Model):
    _name = 'agri.land.use'
    _description = 'Land Use'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    irrigated = fields.Boolean('Irrigated', default=False)
