# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_agri_commodity = fields.Boolean("Is Agri Commodity")
    grading_line_ids = fields.One2many('agri.grading.line', 'product_tmpl_id',
                                       'Grading Components')
    grading_ids = fields.One2many('agri.grading', 'product_tmpl_id', 'Grading')
    grading_count = fields.Integer('# Gradings',
                                   compute='_compute_grading_count',
                                   compute_sudo=False)
    used_in_grading_count = fields.Integer(
        '# of Grading Where is Used',
        compute='_compute_used_in_grading_count',
        compute_sudo=False)

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


class ProductProduct(models.Model):
    _inherit = "product.product"

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
