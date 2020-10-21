from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class ProductionPlan(models.Model):
    _name = 'agri.production.schedule'
    _description = 'Production Plan'
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
    total_mass = fields.Float('Total Mass',
                              compute='_compute_mass',
                              store=True,
                              tracking=True)
    total_yield = fields.Float('Yield',
                               compute='_compute_mass',
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
    period_id = fields.Many2one('date.range.type',
                                string='Period',
                                domain="[('is_calendar_period', '=', True)]",
                                ondelete='cascade',
                                required=True)
    area_uom_id = fields.Many2one(
        'uom.uom',
        'Area Unit',
        domain="[('name', 'in', ['ac', 'ha'])]",
        default=lambda self: self.env.ref('agri.agri_uom_ha'),
        required=True,
        tracking=True)
    mass_uom_id = fields.Many2one(
        'uom.uom',
        'Mass Unit',
        domain="[('name', 'in', ['t', 'kg', 'heads'])]",
        default=lambda self: self.env.ref('uom.product_uom_ton'),
        required=True,
        tracking=True)

    @api.onchange('season_id', 'period_id')
    def _onchange_season_period(self):
        for plan in self:
            plan.line_ids._compute_calendar_period_ids()

    @api.depends('farm_field_ids.area_ha')
    def _compute_total_ha(self):
        for plan in self:
            fields_with_area = plan.farm_field_ids.filtered(
                lambda field: field.area_ha)
            plan.total_ha = sum(fields_with_area.mapped('area_ha'))

    @api.depends('total_ha', 'line_ids', 'area_uom_id', 'mass_uom_id')
    def _compute_mass(self):
        for plan in self:
            quantity = 0.0
            for line in plan.line_ids:
                if (not line.is_purchase and line.product_category_id.uom_id.id
                        == plan.mass_uom_id.id):
                    quantity += line.quantity
            plan.total_mass = plan.total_ha * quantity
            plan.total_yield = (
                plan.total_mass / plan.total_ha if
                not float_is_zero(plan.total_ha,
                                  precision_rounding=plan.area_uom_id.rounding)
                else 0.0)


class ProductionPlanLine(models.Model):
    _name = 'agri.production.schedule.line'
    _description = 'Production Plan Line'
    _order = 'date_range_id asc'

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
    season_id = fields.Many2one(related='production_schedule_id.season_id',
                                readonly=True)
    period_id = fields.Many2one(related='production_schedule_id.period_id',
                                string="Schedule Period",
                                readonly=True)
    calendar_period_ids = fields.One2many(
        'date.range', compute='_compute_calendar_period_ids')
    date_range_id = fields.Many2one(
        'date.range',
        domain="[('id', 'in', calendar_period_ids)]",
        string="Period",
        required=True)
    quantity_uom_id = fields.Many2one(related='product_category_id.uom_id',
                                      string='UoM',
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
    area_uom_id = fields.Many2one(related='production_schedule_id.area_uom_id',
                                  readonly=True)

    @api.depends('season_id', 'period_id')
    @api.onchange('product_category_id', 'season_id', 'period_id')
    def _compute_calendar_period_ids(self):
        for line in self:
            domain = []
            if line.season_id:
                domain += [('id', 'in', line.season_id.calendar_period_ids.ids)
                           ]
            if line.period_id:
                domain += [('type_id', '=', line.period_id.id)]
            line.calendar_period_ids = self.env['date.range'].search(domain)

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
