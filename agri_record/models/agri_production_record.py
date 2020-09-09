from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class AgriProductionRecord(models.Model):
    _name = 'agri.production.record'
    _description = 'Production Record'
    _order = 'name, create_date desc'
    _check_company_auto = True
    name = fields.Char('Record Number',
                       default=lambda self: self.env['ir.sequence'].
                       next_by_code('agri.production.record'),
                       required=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 check_company=True,
                                 required=True)
    company_id = fields.Many2one(related='partner_id.company_id',
                                 index=True,
                                 readonly=True,
                                 store=True)
    field_id = fields.Many2one(
        'agri.field',
        'Field',
        domain=
        "[('active', '=', True), ('farm_id.active', '=', True), ('farm_id.partner_id', '=', partner_id)]",
        ondelete='cascade',
        required=True)
    irrigation_type_id = fields.Many2one(related='field_id.irrigation_type_id',
                                         store=True)
    cultivar_product_id = fields.Many2one(
        'product.product',
        string='Cultivar',
        domain="[('is_cultivar', '=', True)]",
        ondelete='cascade',
        check_company=True,
        required=True)
    # season_id = fields.Many2one('agri.season',
    #                             string='Season',
    #                             ondelete='cascade',
    #                             required=True)
    planted_date = fields.Date('Planted Date')
    planted_ha = fields.Float('Planted Hectares', digits='Hectare')
    delivered_date = fields.Date('Delivered Date')
    delivered_uom_id = fields.Many2one(
        'uom.uom',
        'Delivered Measure',
        domain="[('measure_type', '=', 'weight')]")
    delivered_uom_qty = fields.Float('Delivered Quantity',
                                     digits='Stock Weight')
    delivered_t_ha = fields.Float('Delivered t/Ha',
                                  digits=(8, 6),
                                  compute='_compute_delivered_t_ha',
                                  inverse='_set_delivered_t_ha',
                                  store=True)
    delivered_warehouse_id = fields.Many2one('stock.warehouse',
                                             'Delivery Point',
                                             ondelete='cascade',
                                             check_company=True)

    # _sql_constraints = [
    #     ('production_record_uniq', 'unique(field_id, season_id, delivered_warehouse_id)', 'The production record must be unique!'),
    # ]

    @api.constrains('planted_date', 'planted_ha')
    def _constrains_uom(self):
        if (self.planted_date
                and not self.planted_ha) or (not self.planted_date
                                             and self.planted_ha):
            raise ValidationError('Planted Date and Hectares must be set.')

    @api.constrains('delivered_uom_id', 'delivered_uom_qty')
    def _constrains_uom(self):
        if (self.delivered_uom_id and not self.delivered_uom_qty) or (
                not self.delivered_uom_id and self.delivered_uom_qty):
            raise ValidationError('Delivery Measure and Quantity must be set.')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.field_id and self.field_id.farm_id.partner_id.id != self.partner_id.id:
            self.field_id = None

    @api.onchange('field_id')
    def _onchange_field_id(self):
        if self.field_id:
            self.partner_id = self.field_id.farm_id.partner_id

    @api.onchange('planted_ha', 'delivered_uom_id', 'delivered_uom_qty')
    def _compute_delivered_t_ha(self):
        updated_field = self.env.context.get('updated_field')
        if not updated_field or updated_field not in ['delivered_t_ha']:
            ha_uom_id = self.env['uom.uom'].search([('name', '=', 'ha')],
                                                   limit=1)
            tons_uom_id = self.env['uom.uom'].search([('name', '=', 't')],
                                                     limit=1)
            precision = self.env['decimal.precision'].precision_get(
                'Tons per Hectare')
            for record in self:
                if record.delivered_uom_id and record.planted_ha and not float_is_zero(
                        record.planted_ha,
                        precision_rounding=ha_uom_id.rounding):
                    delivered_tons = record.delivered_uom_id._compute_quantity(
                        record.delivered_uom_qty, tons_uom_id, round=False)
                    record.delivered_t_ha = delivered_tons / record.planted_ha

    @api.onchange('delivered_t_ha')
    def _set_delivered_t_ha(self):
        updated_field = self.env.context.get('updated_field')
        if not updated_field or updated_field not in [
                'planted_ha', 'delivered_uom_id', 'delivered_uom_qty'
        ]:
            ha_uom_id = self.env['uom.uom'].search([('name', '=', 'ha')],
                                                   limit=1)
            tons_uom_id = self.env['uom.uom'].search([('name', '=', 't')],
                                                     limit=1)
            for record in self:
                if record.planted_ha and not record.delivered_uom_qty:
                    if not record.delivered_uom_id:
                        record.delivered_uom_id = tons_uom_id
                    record.delivered_uom_qty = tons_uom_id._compute_quantity(
                        record.delivered_t_ha * record.planted_ha,
                        record.delivered_uom_id,
                        round=False)
                elif record.delivered_uom_id and record.delivered_uom_qty:
                    delivered_tons = record.delivered_uom_id._compute_quantity(
                        record.delivered_uom_qty, tons_uom_id, round=False)
                    record.planted_ha = float_round(
                        delivered_tons / record.delivered_t_ha,
                        precision_rounding=ha_uom_id.rounding,
                        rounding_method='DOWN')
