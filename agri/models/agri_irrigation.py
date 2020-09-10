from odoo import api, fields, models


class IrrigationType(models.Model):
    _name = 'agri.irrigation.type'
    _description = 'Irrigation Type'

    name = fields.Char('Name', required=True)
