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
    partner_farm_version_id = fields.Many2one(
        related='partner_id.farm_version_id',
        string='Partner Farm Version',
        readonly=True)
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
    farm_version_id = fields.Many2one(
        'agri.farm.version',
        'Farm Version',
        domain="[('partner_id', '=', partner_id)]",
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    farm_field_ids = fields.Many2many(
        'agri.farm.field',
        'agri_production_plan_farm_field_rel',
        'production_plan_id',
        'farm_field_id',
        domain="[('farm_id.farm_version_id', '=', farm_version_id)]",
        string='Fields',
        states={'draft': [('readonly', False)]},
        readonly=True,
        copy=False)
    delivery_ids = fields.One2many(comodel_name='agri.delivery',
                                   inverse_name='production_plan_id',
                                   string='Deliveries',
                                   copy=False)
    field_crop_ids = fields.One2many(comodel_name='agri.farm.field.crop',
                                     inverse_name='production_plan_id',
                                     string='Crops',
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
    season_date_start = fields.Date(related='season_id.date_start',
                                    readonly=True)
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

    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for plan in self:
            plan.farm_version_id = plan.partner_id.farm_version_id

    @api.onchange('farm_field_ids')
    def _onchange_farm_field_ids(self):
        for plan in self:
            if not plan.farm_version_id:
                plan.farm_version_id = plan.farm_field_ids.farm_id.farm_version_id

    @api.onchange('season_id', 'period_id')
    def _onchange_season_period(self):
        for plan in self:
            plan.line_ids._compute_calendar_period_ids()

    @api.depends('farm_field_ids.area')
    def _compute_total_land_area(self):
        for plan in self:
            fields_with_area = plan.farm_field_ids.filtered(
                lambda field: field.area)
            plan.total_land_area = sum(fields_with_area.mapped('area'))

    @api.depends('total_land_area', 'line_ids', 'land_uom_id',
                 'consumption_uom_id', 'production_uom_id', 'total_land_area',
                 'line_ids.amount_consumed', 'line_ids.amount_produced',
                 'line_ids.production')
    def _compute_total(self):
        for plan in self:
            amount_produced = 0.0
            amount_consumed = 0.0
            production = 0.0
            for line in plan.line_ids:
                amount_produced += line.amount_produced
                amount_consumed += line.amount_consumed
                production += line.production
            plan.total_production = production
            plan.gross_production_value = amount_produced
            plan.total_costs = amount_consumed
            plan.production_yield = (
                plan.total_production / plan.total_land_area if
                not float_is_zero(plan.total_land_area,
                                  precision_rounding=plan.land_uom_id.rounding)
                else 0.0)

    @api.model
    def _create_crops(self):
        for plan in self:
            plant_lines = plan.line_ids.filtered(
                lambda line: line.product_category_id.cost_type in
                ['crop_establishment', 'crop_input']).sorted(
                    lambda line: line.date_range_id.date_start)
            harvest_lines = plan.line_ids.filtered(
                lambda line: line.product_category_id.cost_type ==
                'crop_harvest').sorted(
                    lambda line: line.date_range_id.date_start)
            sale_lines = plan.line_ids.filtered(
                lambda line: line.product_category_id.cost_type in
                ['crop_sale', 'permanent_crop_sale']).sorted(
                    lambda line: line.date_range_id.date_start)
            if len(plant_lines) == 0:
                raise Warning(_('No crop establishment or input line found'))
            if len(harvest_lines) == 0:
                raise Warning(_('No crop harvest line found'))
            if len(sale_lines) == 0:
                raise Warning(_('No crop sale line found'))
            vals = {
                'harvested_date': harvest_lines[0].date_range_id.date_start,
                'planted_date': plant_lines[0].date_range_id.date_start,
                'product_category_id': sale_lines[0].product_category_id.id,
                'product_id': sale_lines[0].product_id.id,
                'production_plan_id': plan.id
            }
            for field in plan.farm_field_ids:
                vals.update({'field_id': field.id, 'planted_area': field.area})
                crop = self.env['agri.farm.field.crop'].create(vals)

    def action_schedule(self):
        for plan in self:
            plan._create_crops()
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
            ('of_gross_production', '% of gross production'),
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
    production = fields.Float(
        string='Production',
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
                  'application_rate_type')
    @api.depends('price', 'quantity', 'application_rate',
                 'production_plan_id.total_land_area',
                 'production_plan_id.total_production',
                 'production_plan_id.gross_production_value')
    def _compute_subtotal(self):
        period_total_production = 0.0
        for line in self.production_plan_id.line_ids:
            x = line.date_range_id.id
            y = self.date_range_id.id
            if line.date_range_id.id == self.date_range_id.id:
                period_total_production += line.production
        total_land_area = self.production_plan_id.total_land_area
        period_gross_production_value = self.production_plan_id.gross_production_value
        period_total_costs = self.production_plan_id.total_costs
        for line in self:
            # Adjust application rate value if it is a percentage
            application_rate = (line.application_rate /
                                100.0 if line.application_rate_type
                                == 'percentage' else line.application_rate)
            line_production = line.quantity * line.application_rate
            line_value = line.price * line_production
            if line.application_type == 'sum':
                amount_total = line_value
                line.production = line_production
            elif line.application_type == 'per_consumption_unit':
                amount_total = total_land_area * line_value
            elif line.application_type == 'per_production_unit':
                amount_total = period_total_production * line_value
            elif line.application_type == 'of_gross_production':
                amount_total = period_total_production * application_rate * line.price
                line.production = line.quantity
            elif line.application_type == 'of_gross_production_value':
                amount_total = period_gross_production_value * application_rate
            elif line.application_type == 'of_total_costs':
                amount_total = period_total_costs * application_rate
            else:
                amount_total = value
            line.amount_total = amount_total
            # mock
            if line.sale_ok:
                line.amount_produced = amount_total
                line.amount_consumed = 0
            else:
                line.amount_produced = 0
                line.amount_consumed = amount_total
                line.production = 0

    def name_get(self):
        return [(line.id, "{}".format(line.product_category_id.name, ))
                for line in self]

    @api.depends('product_ids.subtotal')
    def _compute_subtotal_cost(self):
        for plan in self:
            products_with_costs = plan.product_ids.filtered(
                lambda product: product.subtotal)
            plan.price = sum(products_with_costs.mapped('subtotal'))
