from odoo import api, fields, models


class AgriLandClass(models.Model):
    _name = 'agri.landclass'
    _description = 'Land Classes'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    irrigated = fields.Boolean('Irrigated', default=False)
