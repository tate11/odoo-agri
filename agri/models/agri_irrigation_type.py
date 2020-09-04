from odoo import api, fields, models


class AgriIrrigationType(models.Model):
    _name = 'agri.irrigationtype'
    _description = 'Irrigation Types'

    name = fields.Char('Name', required=True)
