from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_agri = fields.Boolean('Is Agri', default=False)
    cost_type = fields.Selection(
        [
            ('crop_sale', 'Crop Sales'),
            ('permanent_crop_sale', 'Permanent Crop Sale'),
            ('crop_establishment', 'Crop Establishment'),
            ('crop_input', 'Crop Input'),
            ('crop_harvest', 'Crop Harvest'),
            ('livestock_sale', 'Livestock Sale'),
            ('livestock_product', 'Livestock Product'),
            ('animal_feed', 'Animal Feed'),
            ('husbandry', 'Husbandry'),
            ('livestock_harvest', 'Livestock Harvest'),
            ('overhead', 'Overhead'),
        ],
        string='Cost Type',
        default=False,
    )
    uom_id = fields.Many2one('uom.uom',
                             'Unit of Measure',
                             help='Unit of measure used for allocating costs.')
    sale_ok = fields.Boolean('Can be Sold', default=False)
    purchase_ok = fields.Boolean('Can be Purchased', default=False)

    @api.constrains('cost_type')
    def _check_cost_type(self):
        if self.is_agri and not self.cost_type:
            raise ValidationError(_('Cost Type must be set agricultural product categories'))

    @api.constrains('uom_id')
    def _check_uom_id(self):
        if self.is_agri and not self.uom_id:
            raise ValidationError(_('Unit of Measure must be set agricultural product categories'))

    @api.constrains('cost_type')
    def _check_uom_id(self):
        if self.is_agri and not self.cost_type:
            raise ValidationError(_('The cost type must be set for agricultural product categories'))
