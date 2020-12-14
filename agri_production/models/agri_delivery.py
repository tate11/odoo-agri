from odoo import fields, models


class Delivery(models.Model):
    _inherit = 'agri.delivery'

    production_plan_id = fields.Many2one(
        'agri.production.plan',
        string='Production Plan',
        ondelete='set null',
        states={'draft': [('readonly', False)]},
        readonly=True)
