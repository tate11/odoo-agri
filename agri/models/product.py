from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_agri = fields.Boolean('Is Agri', default=False)
    uom_id = fields.Many2one('uom.uom',
                             'Unit of Measure',
                             help='Unit of measure used for allocating costs.')
    sale_ok = fields.Boolean('Can be Sold', default=False)
    purchase_ok = fields.Boolean('Can be Purchased', default=False)

    @api.constrains('uom_id')
    def _check_uom_id(self):
        if self.is_agri and not self.uom_id:
            raise ValidationError(_('Unit of Measure must be set.'))
