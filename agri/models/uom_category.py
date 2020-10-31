from odoo import fields, models


class UoMCategory(models.Model):
    _inherit = 'uom.category'

    measure_type = fields.Selection(
        selection_add=[('area', 'Default Area'), ('lsu', 'Default LSU')])
