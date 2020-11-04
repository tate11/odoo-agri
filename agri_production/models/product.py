from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_cultivar = fields.Boolean('Is Cultivar', default=False)
    is_catch_weight = fields.Boolean('Is Catch Weight', default=False)
    catch_weight_percent = fields.Float('Catch Weight Percent', default=1)
    leaves_per_plant = fields.Integer('Leaves Per Plant', default=22)
