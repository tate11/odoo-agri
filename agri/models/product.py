from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_agri = fields.Boolean('Is agri?', default=False)
    sale_ok = fields.Boolean('Can be Sold', default=True)
    purchase_ok = fields.Boolean('Can be Purchased', default=True)
