from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class ProductionPlan(models.Model):
    _name = 'agri.production.plan'
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
        'agri_production_plan_farm_field_rel',
        'production_plan_id',
        'farm_field_id',
        domain="[('farm_id.partner_id', '=', partner_id)]",
        string='Fields')
    land_area_uom_id = fields.Many2one(
        'uom.uom',
        'Land Area Unit',
        domain="[('name', 'in', ['ac', 'ha'])]",
        default=lambda self: self.env.ref('agri.agri_uom_ha'),
        required=True,
        tracking=True)
    total_land_area = fields.Float('Total Land Area',
                                   compute='_compute_total_land_area',
                                   store=True,
                                   tracking=True)
    production_uom_id = fields.Many2one(
        'uom.uom',
        'Production Unit',
        domain=
        "[('category_id', 'in', ['agri_category_lsu', 'agri_category_lsu'])]",
        default=lambda self: self.env.ref('uom.product_uom_ton'),
        required=True,
        tracking=True)
    total_production = fields.Float('Total Production',
                                    compute='_compute_production',
                                    store=True,
                                    tracking=True)
    total_production_value = fields.Float('Total Production Value',
                                          compute='_compute_production',
                                          store=True)
    total_yield = fields.Float('Yield',
                               compute='_compute_production',
                               store=True,
                               tracking=True)
    line_ids = fields.One2many(comodel_name='agri.production.plan.line',
                               inverse_name='production_plan_id',
                               string='Production Plan Lines',
                               copy=True)
    season_id = fields.Many2one('date.range',
                                string='Season',
                                ondelete='restrict',
                                domain="[('type_id.is_season', '=', True)]",
                                required=True,
                                tracking=True)
    period_id = fields.Many2one('date.range.type',
                                string='Period',
                                ondelete='restrict',
                                domain="[('is_calendar_period', '=', True)]",
                                required=True)
    consumption_uom_id = fields.Many2one(
        'uom.uom',
        'Consumption Unit',
        domain=
        "[('category_id', 'in', ['agri_category_area', 'agri_category_lsu'])]",
        default=lambda self: self.env.ref('agri.agri_uom_ha'),
        required=True)
    gross_yield = fields.Float('Gross Yield')

    @api.onchange('season_id', 'period_id')
    def _onchange_season_period(self):
        for plan in self:
            plan.line_ids._compute_calendar_period_ids()

    @api.depends('farm_field_ids.area_ha')
    def _compute_total_land_area(self):
        for plan in self:
            fields_with_area = plan.farm_field_ids.filtered(
                lambda field: field.area_ha)
            plan.total_land_area = sum(fields_with_area.mapped('area_ha'))

    @api.depends('total_land_area', 'line_ids', 'land_area_uom_id',
                 'production_uom_id')
    def _compute_production(self):
        for plan in self:
            quantity = 0.0
            for line in plan.line_ids:
                if (not line.is_purchase and line.product_category_id.uom_id.id
                        == plan.production_uom_id.id):
                    quantity += line.no_of_times * line.application_rate
            plan.total_production = plan.total_land_area * quantity
            plan.total_yield = (
                plan.total_production /
                plan.total_land_area if not float_is_zero(
                    plan.total_land_area,
                    precision_rounding=plan.land_area_uom_id.rounding) else
                0.0)


class ProductionPlanLine(models.Model):
    _name = 'agri.production.plan.line'
    _description = 'Production Plan Line'
    _order = 'date_range_id asc'

    sale_ok = fields.Boolean(related='product_category_id.sale_ok',
                             store=False)
    purchase_ok = fields.Boolean(related='product_category_id.purchase_ok',
                                 store=False)
    production_plan_id = fields.Many2one('agri.production.plan',
                                         string='Production Plan',
                                         ondelete='cascade',
                                         required=True)
    season_id = fields.Many2one(related='production_plan_id.season_id',
                                readonly=True)
    period_id = fields.Many2one(related='production_plan_id.period_id',
                                string='Plan Period',
                                readonly=True)
    calendar_period_ids = fields.One2many(
        'date.range', compute='_compute_calendar_period_ids')
    date_range_id = fields.Many2one(
        'date.range',
        string='Period',
        ondelete='restrict',
        domain="[('id', 'in', calendar_period_ids)]",
        required=True)
    product_category_id = fields.Many2one('product.category',
                                          string='Category',
                                          domain="[('is_agri', '=', True)]",
                                          ondelete='cascade',
                                          required=True)
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 required=True)

    is_purchase = fields.Boolean('Is Purchase', default='_compute_is_purchase')
    price = fields.Float(string='Price', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True)
    product_uom_id = fields.Many2one('uom.uom',
                                     string='Purchase UoM',
                                     required=True)
    payment_term_id = fields.Many2one("account.payment.term",
                                      string="Payment Terms",
                                      required=True)
    land_area_uom_id = fields.Many2one(
        related='production_plan_id.land_area_uom_id', readonly=True)
    application_type = fields.Selection(
        [
            ("sum", "Sum"),
            ("per_land_unit", "Per land unit"),
            ("per_consumption_unit", "Per consumption unit"),
            ("per_production_unit", "Per production unit"),
            ("perc_of_production_value", "Percentage of production value"),
        ],
        string="Application Type",
        required=True,
        default="per_land_unit",
    )
    application_uom_id = fields.Many2one(related='product_category_id.uom_id',
                                         string='Application UoM')
    application_rate = fields.Float('Application Rate',
                                    default=1,
                                    digits='Stock Weight')
    no_of_times = fields.Float('No of times', default=1, digits='Stock Weight')
    total = fields.Monetary(string='Total',
                            compute='_compute_total',
                            store=True)

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

    @api.onchange('no_of_times', 'price')
    @api.depends('no_of_times', 'price', 'production_plan_id.total_land_area')
    def _compute_total(self):
        for line in self:
            if line.application_type == 'variable':
                line_total = line.price * line.production_plan_id.total_land_area * (
                    line.no_of_times or 1.0) * (line.application_rate or 1.0)
            else:
                line_total = line.price * (line.application_rate
                                           or 1.0) * (line.no_of_times or 1.0)
            line.total = line_total

    def name_get(self):
        return [(line.id, "{}".format(line.product_category_id.name, ))
                for line in self]

    @api.depends('product_ids.subtotal')
    def _compute_total_cost(self):
        for plan in self:
            products_with_costs = plan.product_ids.filtered(
                lambda product: product.subtotal)
            plan.price = sum(products_with_costs.mapped('subtotal'))
