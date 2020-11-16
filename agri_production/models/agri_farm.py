from odoo import fields, models


class FarmFieldCrop(models.Model):
    _inherit = 'agri.farm.field.crop'

    production_plan_id = fields.Many2one('agri.production.plan',
                                         string='Production Plan',
                                         ondelete='set null')
