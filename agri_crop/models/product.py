from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_cultivar = fields.Boolean('Is Cultivar', default=False)
    leaves_per_plant = fields.Integer('Leaves Per Plant', default=22)
