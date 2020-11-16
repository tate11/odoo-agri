# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero


class ProductTemplate(models.Model):
    _inherit = "product.template"

    grading_line_ids = fields.One2many('agri.grading.line', 'product_tmpl_id', 'Grading Components')
    grading_ids = fields.One2many('agri.grading', 'product_tmpl_id', 'Grading')
    grading_count = fields.Integer('# Gradings',
                                   compute='_compute_grading_count', compute_sudo=False)
    used_in_grading_count = fields.Integer('# of Grading Where is Used',
                                       compute='_compute_used_in_grading_count', compute_sudo=False)

    def _compute_grading_count(self):
        for product in self:
            product.grading_count = self.env['agri.grading'].search_count([('product_tmpl_id', '=', product.id)])

    def _compute_used_in_grading_count(self):
        for template in self:
            template.used_in_grading_count = self.env['agri.grading'].search_count(
                [('grading_line_ids.product_id', 'in', template.product_variant_ids.ids)])

    def action_used_in_grading(self):
        self.ensure_one()
        action = self.env.ref('agri_commodity.agri_grading_action_form').read()[0]
        action['domain'] = [('grading_line_ids.product_id', 'in', self.product_variant_ids.ids)]
        return action

    def _compute_quantities(self):
        """ When the product template is a kit, this override computes the fields :
         - 'virtual_available'
         - 'qty_available'
         - 'incoming_qty'
         - 'outgoing_qty'
         - 'free_qty'
        """
        product_without_grading = self.browse([])
        for product_template in self:
            if not self.env['agri.grading']._grading_find(product_tmpl=product_template):
                product_without_grading |= product_template
                continue
            virtual_available = 0
            qty_available = 0
            incoming_qty = 0
            outgoing_qty = 0
            free_qty = 0
            for product in product_template.product_variant_ids:
                if self.env['agri.grading']._grading_find(product=product):
                    qty_available += product.qty_available
                    virtual_available += product.virtual_available
                    incoming_qty += product.incoming_qty
                    outgoing_qty += product.outgoing_qty
                    free_qty += product.free_qty
            product_template.qty_available = qty_available
            product_template.virtual_available = virtual_available
            product_template.incoming_qty = incoming_qty
            product_template.outgoing_qty = outgoing_qty
            product_template.free_qty = free_qty

        super(ProductTemplate, product_without_grading)._compute_quantities()


class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_grading_ids = fields.One2many('agri.grading', 'product_id', 'Grading Product Variants')
    grading_line_ids = fields.One2many('agri.grading.line', 'product_id', 'Grading Components')
    grading_count = fields.Integer('# Gradings',
        compute='_compute_grading_count', compute_sudo=False)
    used_in_grading_count = fields.Integer('# BoM Where Used',
        compute='_compute_used_in_grading_count', compute_sudo=False)

    def _compute_grading_count(self):
        for product in self:
            product.grading_count = self.env['agri.grading'].search_count(['|', ('product_id', '=', product.id), '&', ('product_id', '=', False), ('product_tmpl_id', '=', product.product_tmpl_id.id)])

    def _compute_used_in_grading_count(self):
        for product in self:
            product.used_in_grading_count = self.env['agri.grading'].search_count([('grading_line_ids.product_id', '=', product.id)])

    def get_components(self):
        """ Return the components list ids in case of kit product.
        Return the product itself otherwise"""
        self.ensure_one()
        grading_kit = self.env['agri.grading']._grading_find(product=self)
        if grading_kit:
            gradings, grading_sub_lines = grading_kit.explode(self, 1)
            return [grading_line.product_id.id for grading_line, data in grading_sub_lines if grading_line.product_id.type == 'product']
        else:
            return super(ProductProduct, self).get_components()

    def action_used_in_grading(self):
        self.ensure_one()
        action = self.env.ref('mrp.mrp_bom_form_action').read()[0]
        action['domain'] = [('grading_line_ids.product_id', '=', self.id)]
        return action

    def _compute_quantities(self):
        """ When the product is a kit, this override computes the fields :
         - 'virtual_available'
         - 'qty_available'
         - 'incoming_qty'
         - 'outgoing_qty'
         - 'free_qty'
        """
        self.virtual_available = 0
        self.qty_available = 0
        self.incoming_qty = 0
        self.outgoing_qty = 0
        self.free_qty = 0
        grading_kits = {
            product: grading
            for product in self
            for grading in (self.env['agri.grading']._grading_find(product=product),)
            if grading
        }
        kits = self.filtered(lambda p: grading_kits.get(p))
        super(ProductProduct, self.filtered(lambda p: p not in grading_kits))._compute_quantities()
        for product in grading_kits:
            gradings, grading_sub_lines = grading_kits[product].explode(product, 1)
            ratios_virtual_available = []
            ratios_qty_available = []
            ratios_incoming_qty = []
            ratios_outgoing_qty = []
            ratios_free_qty = []
            for grading_line, grading_line_data in grading_sub_lines:
                component = grading_line.product_id
                if component.type != 'product' or float_is_zero(grading_line_data['qty'], precision_rounding=grading_line.product_uom_id.rounding):
                    # As BoMs allow components with 0 qty, a.k.a. optionnal components, we simply skip those
                    # to avoid a division by zero. The same logic is applied to non-storable products as those
                    # products have 0 qty available.
                    continue
                uom_qty_per_kit = grading_line_data['qty'] / grading_line_data['original_qty']
                qty_per_kit = grading_line.product_uom_id._compute_quantity(uom_qty_per_kit, grading_line.product_id.uom_id)
                ratios_virtual_available.append(component.virtual_available / qty_per_kit)
                ratios_qty_available.append(component.qty_available / qty_per_kit)
                ratios_incoming_qty.append(component.incoming_qty / qty_per_kit)
                ratios_outgoing_qty.append(component.outgoing_qty / qty_per_kit)
                ratios_free_qty.append(component.free_qty / qty_per_kit)
            if grading_sub_lines and ratios_virtual_available:  # Guard against all cnsumable grading: at least one ratio should be present.
                product.virtual_available = min(ratios_virtual_available) // 1
                product.qty_available = min(ratios_qty_available) // 1
                product.incoming_qty = min(ratios_incoming_qty) // 1
                product.outgoing_qty = min(ratios_outgoing_qty) // 1
                product.free_qty = min(ratios_free_qty) // 1

    def action_view_grading(self):
        action = self.env.ref('agri_commodity.product_open_bom').read()[0]
        template_ids = self.mapped('product_tmpl_id').ids
        # bom specific to this variant or global to template
        action['context'] = {
            'default_product_tmpl_id': template_ids[0],
            'default_product_id': self.ids[0],
        }
        action['domain'] = ['|', ('product_id', 'in', self.ids), '&', ('product_id', '=', False), ('product_tmpl_id', 'in', template_ids)]
        return action

