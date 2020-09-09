from odoo import api, fields, models


class AgriLandClass(models.Model):
    _name = 'agri.land.class'
    _description = 'Land Classe'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    irrigated = fields.Boolean('Irrigated', default=False)
