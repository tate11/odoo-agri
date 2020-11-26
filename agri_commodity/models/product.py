from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_agri_commodity = fields.Boolean('Is Agri Commodity')
    delivery_loss_perc = fields.Float('Delivery Loss Percent',
                                      default=0.0,
                                      digits=(3, 2))
    default_grading_id = fields.Many2one('agri.grading', string='Default Grading')
    default_grading_line_ids = fields.One2many(
        related='default_grading_id.grading_line_ids', readonly=False)
    default_grading_byproduct_ids = fields.One2many(
        related='default_grading_id.byproduct_ids', readonly=False)
    grading_ids = fields.One2many('agri.grading', 'product_tmpl_id', 'Grading')
    grading_line_ids = fields.One2many('agri.grading.line', 'product_tmpl_id',
                                       'Grading Components')
    grading_count = fields.Integer('# Gradings',
                                   compute='_compute_grading_count',
                                   compute_sudo=False)
    used_in_grading_count = fields.Integer(
        '# of Grading Where is Used',
        compute='_compute_used_in_grading_count',
        compute_sudo=False)

    @api.constrains('delivery_loss_perc')
    def _check_delivery_loss_perc(self):
        for product in self:
            if product.delivery_loss_perc < 0 or product.delivery_loss_perc > 100:
                raise ValidationError(
                    _('Delivery Loss Percent must be from 0 to 100'))

    def _compute_grading_count(self):
        for product in self:
            product.grading_count = self.env['agri.grading'].search_count([
                ('product_tmpl_id', '=', product.id)
            ])

    def _compute_used_in_grading_count(self):
        for template in self:
            template.used_in_grading_count = self.env[
                'agri.grading'].search_count([
                    ('grading_line_ids.product_id', 'in',
                     template.product_variant_ids.ids)
                ])

    def action_used_in_grading(self):
        self.ensure_one()
        action = self.env.ref(
            'agri_commodity.agri_grading_action_form').read()[0]
        action['domain'] = [('grading_line_ids.product_id', 'in',
                             self.product_variant_ids.ids)]
        return action

    @api.model
    def create(self, vals):
        product = super(ProductTemplate, self).create(vals)
        if product.is_agri_commodity and not product.default_grading_id:
            grading = self.env['agri.grading'].create({
                'product_tmpl_id':
                product.id,
                'product_uom_id':
                product.uom_id.id,
                'grading_line_ids':
                vals['default_grading_line_ids']
                if 'default_grading_line_ids' in vals else [],
                'byproduct_ids':
                vals['default_grading_byproduct_ids']
                if 'default_grading_byproduct_ids' in vals else [],
            })
            product.write({'default_grading_id': grading.id})
        return product

    def write(self, vals):
        if 'is_agri_commodity' in vals:
            if not vals['is_agri_commodity']:
                self.default_grading_id.unlink()
                vals.update({'default_grading_id': False})
            elif not self.default_grading_id:
                grading = self.env['agri.grading'].create({
                    'product_tmpl_id':
                    self.id,
                    'product_uom_id':
                    self.uom_id.id,
                    'grading_line_ids':
                    vals['default_grading_line_ids']
                    if 'default_grading_line_ids' in vals else [],
                    'byproduct_ids':
                    vals['default_grading_byproduct_ids']
                    if 'default_grading_byproduct_ids' in vals else [],
                })
                vals.update({'default_grading_id': grading.id})
        return super(ProductTemplate, self).write(vals)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    variant_grading_ids = fields.One2many('agri.grading', 'product_id',
                                          'Grading Product Variants')
    grading_line_ids = fields.One2many('agri.grading.line', 'product_id',
                                       'Grading Components')
    grading_count = fields.Integer('# Gradings',
                                   compute='_compute_grading_count',
                                   compute_sudo=False)
    used_in_grading_count = fields.Integer(
        '# BoM Where Used',
        compute='_compute_used_in_grading_count',
        compute_sudo=False)

    def _compute_grading_count(self):
        for product in self:
            product.grading_count = self.env['agri.grading'].search_count([
                '|', ('product_id', '=', product.id), '&',
                ('product_id', '=', False),
                ('product_tmpl_id', '=', product.product_tmpl_id.id)
            ])

    def _compute_used_in_grading_count(self):
        for product in self:
            product.used_in_grading_count = self.env[
                'agri.grading'].search_count([('grading_line_ids.product_id',
                                               '=', product.id)])

    def action_used_in_grading(self):
        self.ensure_one()
        action = self.env.ref(
            'agri_commodity.agri_grading_action_form').read()[0]
        action['domain'] = [('grading_line_ids.product_id', '=', self.id)]
        return action

    def action_view_grading(self):
        action = self.env.ref('agri_commodity.product_open_bom').read()[0]
        template_ids = self.mapped('product_tmpl_id').ids
        # bom specific to this variant or global to template
        action['context'] = {
            'default_product_tmpl_id': template_ids[0],
            'default_product_id': self.ids[0],
        }
        action['domain'] = [
            '|', ('product_id', 'in', self.ids), '&',
            ('product_id', '=', False), ('product_tmpl_id', 'in', template_ids)
        ]
        return action
