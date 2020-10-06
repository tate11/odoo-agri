from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class ProductionRecord(models.Model):
    _name = 'agri.production.record'
    _description = 'Production Record'
    _order = 'name, create_date desc'
    _check_company_auto = True

    name = fields.Char('Record Number',
                       default=lambda self: self.env['ir.sequence'].
                       next_by_code('agri.production.record'),
                       required=True)
    source = fields.Selection([('average', 'Average'), ('import', 'Import'),
                               ('schedule', 'Production Schedule')],
                              string='Source',
                              default='import',
                              required=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 check_company=True,
                                 required=True)
    company_id = fields.Many2one('res.company',
                                 required=True,
                                 default=lambda self: self.env.company)
    production_schedule_id = fields.Many2one(
        comodel_name="agri.production.schedule",
        string="Production Schedule",
        ondelete='cascade',
        check_company=True)
    farm_field_id = fields.Many2one(
        'agri.farm.field',
        'Field',
        domain=
        "[('active', '=', True), ('farm_id.active', '=', True), ('farm_id.partner_id', '=', partner_id)]",
        ondelete='cascade',
        required=True)
    irrigation_type_id = fields.Many2one(
        related='farm_field_id.irrigation_type_id', store=True)
    cultivar_product_id = fields.Many2one(
        'product.product',
        string='Cultivar',
        domain="[('is_cultivar', '=', True)]",
        ondelete='cascade',
        check_company=True,
        required=True)
    season_id = fields.Many2one('date.range',
                                string='Season',
                                domain="[('type_id.is_season', '=', True)]",
                                ondelete='cascade',
                                required=True)
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
                                  readonly=False,
                                  store=True)
    delivered_warehouse_id = fields.Many2one('stock.warehouse',
                                             'Delivery Point',
                                             ondelete='cascade',
                                             check_company=True)

    _sql_constraints = [
        ('production_record_uniq',
         'unique(farm_field_id, season_id, delivered_warehouse_id)',
         'The production record must be unique!'),
    ]

    @api.onchange('planted_ha', 'delivered_uom_id', 'delivered_uom_qty')
    def _compute_delivered_t_ha(self):
        updated_field = self.env.context.get('updated_field')
        if not updated_field or updated_field not in ['delivered_t_ha']:
            ha_uom = self.env.ref('agri.agri_uom_ha')
            ton_uom = self.env.ref('uom.product_uom_ton')
            precision = self.env['decimal.precision'].precision_get(
                'Tons per Hectare')
            for record in self:
                if record.delivered_uom_id and record.planted_ha and not float_is_zero(
                        record.planted_ha, precision_rounding=ha_uom.rounding):
                    delivered_tons = record.delivered_uom_id._compute_quantity(
                        record.delivered_uom_qty, ton_uom, round=False)
                    record.delivered_t_ha = delivered_tons / record.planted_ha

    @api.onchange('delivered_t_ha')
    def _onchange_delivered_t_ha(self):
        updated_field = self.env.context.get('updated_field')
        if not updated_field or updated_field not in [
                'planted_ha', 'delivered_uom_id', 'delivered_uom_qty'
        ]:
            ha_uom = self.env.ref('agri.agri_uom_ha')
            ton_uom = self.env.ref('uom.product_uom_ton')
            for record in self:
                if record.planted_ha and not record.delivered_uom_qty:
                    if not record.delivered_uom_id:
                        record.delivered_uom_id = ton_uom
                    record.delivered_uom_qty = ton_uom._compute_quantity(
                        record.delivered_t_ha * record.planted_ha,
                        record.delivered_uom_id,
                        round=False)
                elif record.delivered_uom_id and record.delivered_uom_qty:
                    delivered_tons = record.delivered_uom_id._compute_quantity(
                        record.delivered_uom_qty, ton_uom, round=False)
                    record.planted_ha = float_round(
                        delivered_tons / record.delivered_t_ha,
                        precision_rounding=ha_uom.rounding,
                        rounding_method='DOWN')

    @api.constrains('delivered_uom_id', 'delivered_uom_qty')
    def _check_delivered(self):
        if (self.delivered_uom_id and not self.delivered_uom_qty) or (
                not self.delivered_uom_id and self.delivered_uom_qty):
            raise ValidationError(
                _('Delivery Measure and Quantity must be set.'))

    @api.onchange('farm_field_id')
    def _onchange_farm_field_id(self):
        if self.farm_field_id:
            self.partner_id = self.farm_field_id.farm_id.partner_id

    @api.constrains('planted_date', 'planted_ha')
    def _check_planted(self):
        if (self.planted_date
                and not self.planted_ha) or (not self.planted_date
                                             and self.planted_ha):
            raise ValidationError(_('Planted Date and Hectares must be set.'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and self.farm_field_id and self.farm_field_id.farm_id.partner_id.id != self.partner_id.id:
            self.farm_field_id = None

    @api.onchange('production_schedule_id')
    def _onchange_production_schedule_id(self):
        self.source = 'schedule' if self.production_schedule_id else 'import'

    @api.onchange('source')
    def _onchange_source(self):
        if self.source != 'schedule':
            self.production_schedule_id = None

    @api.constrains('source', 'production_schedule_id')
    def _check_source(self):
        if self.source == 'schedule' and not self.production_schedule_id:
            raise ValidationError(_('Production Schedule must be set.'))
        elif self.source != 'schedule' and self.production_schedule_id:
            raise ValidationError(
                _('Source must be set to Production Schedule.'))


class ProductionSchedule(models.Model):
    _name = 'agri.production.schedule'
    _description = 'Production Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    name = fields.Char('Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 check_company=True,
                                 required=True)
    company_id = fields.Many2one('res.company',
                                 required=True,
                                 default=lambda self: self.env.company)
    farm_field_ids = fields.Many2many(
        'agri.farm.field',
        'agri_production_schedule_farm_field_rel',
        'production_schedule_id',
        'farm_field_id',
        domain="[('farm_id.partner_id', '=', partner_id)]",
        string='Fields')
    total_ha = fields.Float('Total Hectares',
                            compute='_compute_total_ha',
                            store=True,
                            tracking=True)
    total_yield = fields.Float('Total Yield',
                               compute='_compute_total_yield',
                               store=True,
                               tracking=True)
    line_ids = fields.One2many(comodel_name='agri.production.schedule.line',
                               inverse_name='production_schedule_id',
                               string='Production Schedule Lines',
                               copy=True)
    season_id = fields.Many2one('date.range',
                                string='Season',
                                domain="[('type_id.is_season', '=', True)]",
                                ondelete='cascade',
                                required=True,
                                tracking=True)
    unit_uom_id = fields.Many2one('uom.uom',
                                  'Unit',
                                  domain="[('measure_type', '=', 'area')]",
                                  required=True,
                                  tracking=True)

    @api.depends('farm_field_ids.area_ha')
    def _compute_total_ha(self):
        for plan in self:
            fields_with_area = plan.farm_field_ids.filtered(
                lambda field: field.area_ha)
            plan.total_ha = sum(fields_with_area.mapped('area_ha'))

    @api.depends('total_ha', 'line_ids')
    def _compute_total_yield(self):
        ton_uom = self.env.ref('uom.product_uom_ton')
        for plan in self:
            total_yield = 0.0
            for line in plan.line_ids:
                if not line.is_purchase and line.product_category_id.uom_id.id == ton_uom.id:
                    total_yield += line.quantity
            plan.total_yield = plan.total_ha * total_yield


class ProductionScheduleLine(models.Model):
    _name = 'agri.production.schedule.line'
    _description = 'Production Schedule Line'
    _order = 'date asc'

    product_category_id = fields.Many2one('product.category',
                                          string='Category',
                                          domain="[('is_agri', '=', True)]",
                                          ondelete='cascade',
                                          required=True)
    sale_ok = fields.Boolean(related='product_category_id.sale_ok',
                             store=False)
    purchase_ok = fields.Boolean(related='product_category_id.purchase_ok',
                                 store=False)
    production_schedule_id = fields.Many2one('agri.production.schedule',
                                             string='Production Schedule',
                                             ondelete='cascade',
                                             required=True)
    date = fields.Date('Date', required=True)
    quantity_uom_id = fields.Many2one(related='product_category_id.uom_id',
                                      string='Quantity Units',
                                      readonly=True)
    quantity = fields.Float('Quantity', digits='Stock Weight')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True)
    amount = fields.Monetary(string='Price', required=True)
    total = fields.Monetary(string='Total',
                            compute='_compute_total',
                            store=True)
    is_purchase = fields.Boolean('Is Purchase', default='_compute_is_purchase')
    unit_uom_id = fields.Many2one(related='production_schedule_id.unit_uom_id',
                                  readonly=True)

    @api.onchange('product_category_id')
    def _compute_is_purchase(self):
        for line in self:
            line.is_purchase = (line.product_category_id.purchase_ok
                                and not line.product_category_id.sale_ok
                                ) if line.product_category_id else False

    @api.onchange('quantity', 'amount')
    @api.depends('quantity', 'amount', 'production_schedule_id.total_ha')
    def _compute_total(self):
        for line in self:
            line.total = line.amount * line.production_schedule_id.total_ha * (
                line.quantity or 1.0)

    def name_get(self):
        return [(line.id, "{}".format(line.product_category_id.name, ))
                for line in self]
