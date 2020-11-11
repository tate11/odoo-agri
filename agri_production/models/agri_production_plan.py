from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class ProductionPlan(models.Model):
    _name = 'agri.production.plan'
    _description = 'Production Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    name = fields.Char('Name',
                       states={'draft': [('readonly', False)]},
                       readonly=True,
                       required=True,
                       tracking=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 states={'draft': [('readonly', False)]},
                                 readonly=True,
                                 required=True)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]},
                                 readonly=True,
                                 required=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    enterprise_type = fields.Selection([('crop', 'Crop'),
                                        ('permanent_crop', 'Permanent Crop'),
                                        ('livestock', 'Livestock')],
                                       string='Type',
                                       default='crop',
                                       states={'draft': [('readonly', False)]},
                                       readonly=True,
                                       required=True)
    farm_field_ids = fields.Many2many(
        'agri.farm.field',
        'agri_production_plan_farm_field_rel',
        'production_plan_id',
        'farm_field_id',
        domain="[('farm_id.partner_id', '=', partner_id)]",
        string='Fields',
        states={'draft': [('readonly', False)]},
        readonly=True,
        copy=False)
    land_uom_id = fields.Many2one(
        'uom.uom',
        'Land Area Unit',
        domain="[('name', 'in', ['ac', 'ha'])]",
        default=lambda self: self.env.ref('agri.agri_uom_ha'),
        states={'draft': [('readonly', False)]},
        readonly=True,
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
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        tracking=True)
    total_production = fields.Float('Total Production',
                                    compute='_compute_total',
                                    store=True,
                                    tracking=True)
    gross_production_value = fields.Monetary('Gross Production Value',
                                             compute='_compute_total',
                                             store=True)
    production_yield = fields.Float('Yield',
                                    compute='_compute_total',
                                    store=True,
                                    tracking=True)
    total_costs = fields.Monetary('Total costs',
                                  compute='_compute_total',
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
                                states={'draft': [('readonly', False)]},
                                readonly=True,
                                tracking=True,
                                copy=False)
    period_id = fields.Many2one('date.range.type',
                                string='Period',
                                ondelete='restrict',
                                domain="[('is_calendar_period', '=', True)]",
                                states={'draft': [('readonly', False)]},
                                readonly=True,
                                required=True,
                                tracking=True)
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Payment Terms',
        default=lambda self: self.env.ref(
            'account.account_payment_term_immediate'),
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        tracking=True)
    consumption_uom_id = fields.Many2one(
        'uom.uom',
        'Consumption Unit',
        domain=
        "[('category_id', 'in', ['agri_category_area', 'agri_category_lsu'])]",
        default=lambda self: self.env.ref('agri.agri_uom_ha'),
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        tracking=True)
    gross_yield = fields.Float('Gross Yield', tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('scheduled', 'Scheduled'),
                                        ('done', 'Done')],
                             string='State',
                             default='draft',
                             readonly=True,
                             copy=False,
                             tracking=True)

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

    @api.depends('total_land_area', 'line_ids', 'land_uom_id',
                 'consumption_uom_id', 'production_uom_id', 'total_land_area',
                 'line_ids.amount_consumed', 'line_ids.amount_produced',
                 'line_ids.quantity_produced')
    def _compute_total(self):
        for plan in self:
            amount_produced = 0.0
            amount_consumed = 0.0
            quantity_produced = 0.0
            for line in plan.line_ids:
                amount_produced += line.amount_produced
                amount_consumed += line.amount_consumed
                quantity_produced += line.quantity_produced
            plan.total_production = quantity_produced
            plan.gross_production_value = amount_produced
            plan.total_costs = amount_consumed
            plan.production_yield = (
                plan.total_production / plan.total_land_area if
                not float_is_zero(plan.total_land_area,
                                  precision_rounding=plan.land_uom_id.rounding)
                else 0.0)

    def action_schedule(self):
        for plan in self:
            plan.state = 'scheduled'
            plan.line_ids._compute_state()

    def action_done(self):
        for plan in self:
            plan.state = 'done'
            plan.line_ids._compute_state()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('name', _("%s (copy)") % (self.name, ))
        return super(ProductionPlan, self).copy(default)


class ProductionPlanLine(models.Model):
    _name = 'agri.production.plan.line'
    _description = 'Production Plan Line'
    _order = 'date_range_id asc'

    # TODO: Return product default CW%
    @api.model
    def _get_default_catch_weight_percent(self):
        return 12.5

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
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    product_category_id = fields.Many2one(
        'product.category',
        string='Category',
        domain="[('is_agri', '=', True)]",
        ondelete='cascade',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 domain="[('categ_id.is_agri', '=', True)]",
                                 states={'draft': [('readonly', False)]},
                                 readonly=True,
                                 required=True)
    is_purchase = fields.Boolean('Is Purchase', default='_compute_is_purchase')
    price = fields.Monetary(string='Price',
                            states={'draft': [('readonly', False)]},
                            readonly=True,
                            required=True)
    currency_id = fields.Many2one(related='production_plan_id.currency_id',
                                  readonly=True)
    product_uom_id = fields.Many2one('uom.uom',
                                     string='Purchase UoM',
                                     states={'draft': [('readonly', False)]},
                                     readonly=True,
                                     required=True)
    payment_term_id = fields.Many2one(
        'account.payment.term',
        default=lambda self: self.production_plan_id.payment_term_id,
        string='Payment Terms',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    land_uom_id = fields.Many2one(related='production_plan_id.land_uom_id',
                                  readonly=True)
    production_uom_id = fields.Many2one(
        related='production_plan_id.production_uom_id', readonly=True)
    consumption_uom_id = fields.Many2one(
        related='production_plan_id.consumption_uom_id', readonly=True)
    application_type = fields.Selection(
        [
            ('sum', 'Sum'),
            ('per_production_unit', 'Per production unit'),
            ('per_consumption_unit', 'Per consumption unit'),
            ('of_gross_production_value', '% of gross production value'),
            ('of_total_costs', '% of total costs'),
        ],
        string='Application Type',
        default='sum',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
    )
    quantity = fields.Float('Quantity',
                            default=1,
                            digits='Stock Weight',
                            states={'draft': [('readonly', False)]},
                            readonly=True)
    application_uom_id = fields.Many2one(related='product_category_id.uom_id',
                                         string='Application UoM')
    application_rate = fields.Float('Application Rate',
                                    default=1,
                                    digits='Stock Weight',
                                    states={'draft': [('readonly', False)]},
                                    readonly=True)
    application_rate_type = fields.Selection(
        [('percentage', '%'), ('no_of_times', 'no. of times')],
        string='Application Rate Type',
        default='no_of_times',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    is_catch_weight = fields.Boolean('Is Catch Weight',
                                     related='product_id.is_catch_weight')
    catch_weight_percent = fields.Float(
        'Catch Weight Percent',
        default=lambda self: self._get_default_catch_weight_percent(),
        states={'draft': [('readonly', False)]},
        readonly=True)
    amount_total = fields.Monetary(string='Total',
                                   compute='_compute_subtotal',
                                   store=True)
    amount_produced = fields.Monetary(string='Amount Produced',
                                      compute='_compute_subtotal',
                                      store=True,
                                      help="The value produced by this item")
    amount_consumed = fields.Monetary(
        string='Amount Consumed',
        compute='_compute_subtotal',
        store=True,
        help="The value consumed by this expense")
    quantity_produced = fields.Float(
        string='Quantity Produced',
        compute='_compute_subtotal',
        store=True,
        help="The production quantity measured in the production UoM")
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('scheduled', 'Scheduled'),
                                        ('done', 'Done')],
                             string='State',
                             default='draft',
                             readonly=True,
                             copy=False)

    @api.depends('production_plan_id.state')
    def _compute_state(self):
        for line in self:
            if line.state == 'draft':
                line.state = line.production_plan_id.state

    @api.depends('production_plan_id')
    @api.onchange('product_category_id', 'production_plan_id')
    def _compute_payment_term_id(self):
        for line in self:
            if line.production_plan_id and not line.payment_term_id:
                line.payment_term_id = line.production_plan_id.payment_term_id

    @api.onchange('product_id')
    def _compute_product_price_uom(self):
        for line in self:
            if line.product_id:
                line.product_category_id = line.product_id.categ_id or line.product_category_id
                line.price = line.product_id.lst_price or line.price
                line.product_uom_id = line.product_id.uom_id or line.product_uom

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

    @api.onchange('price', 'quantity', 'application_type', 'application_rate',
                  'application_rate_type', 'catch_weight_percent')
    @api.depends('price', 'quantity', 'application_rate',
                 'catch_weight_percent', 'production_plan_id.total_land_area',
                 'production_plan_id.total_production',
                 'production_plan_id.gross_production_value')
    def _compute_subtotal(self):
        total_land_area = self.production_plan_id.total_land_area
        total_production = self.production_plan_id.total_production
        gross_production_value = self.production_plan_id.gross_production_value
        total_costs = self.production_plan_id.total_costs
        for line in self:
            total_land_area = line.production_plan_id.total_land_area
            total_production = line.production_plan_id.total_production
            gross_production_value = line.production_plan_id.gross_production_value
            total_costs = line.production_plan_id.total_costs
            # Adjust priced based on catch weight percent
            price = (line.price * line.catch_weight_percent /
                     100.0 if line.is_catch_weight else line.price)
            quantity = line.quantity or 1.0
            # Adjust application rate value if it is a percentage
            application_rate = (line.application_rate /
                                100.0 if line.application_rate_type
                                == 'percentage' else line.application_rate)
            value = price * quantity * application_rate
            if line.application_type == 'sum':
                amount_total = value
            elif line.application_type == 'per_consumption_unit':
                amount_total = total_land_area * value
            elif line.application_type == 'per_production_unit':
                amount_total = total_production * value
            elif line.application_type == 'of_gross_production_value':
                amount_total = gross_production_value * application_rate
            elif line.application_type == 'of_total_costs':
                amount_total = total_costs * application_rate
            else:
                amount_total = value
            line.amount_total = amount_total
            # mock
            if line.sale_ok is True:
                line.amount_produced = amount_total
                line.amount_consumed = 0
                line.quantity_produced = quantity * application_rate
            else:
                line.amount_produced = 0
                line.amount_consumed = amount_total

    def name_get(self):
        return [(line.id, "{}".format(line.product_category_id.name, ))
                for line in self]

    @api.depends('product_ids.subtotal')
    def _compute_subtotal_cost(self):
        for plan in self:
            products_with_costs = plan.product_ids.filtered(
                lambda product: product.subtotal)
            plan.price = sum(products_with_costs.mapped('subtotal'))
