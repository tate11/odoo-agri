from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class Delivery(models.Model):
    _name = 'agri.delivery'
    _description = 'Delivery'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    name = fields.Char(compute='_compute_name',
                       string='Name',
                       store=True,
                       copy=False)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 states={'draft': [('readonly', False)]},
                                 readonly=True,
                                 required=True)
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 index=True,
                                 default=lambda self: self.env.company)
    advance_payment_date = fields.Date(string='Advance Payment Date',
                                       states={'draft': [('readonly', False)]},
                                       readonly=True,
                                       copy=False,
                                       tracking=True)
    delivery_date = fields.Date(string='Delivery Date',
                                states={'draft': [('readonly', False)]},
                                readonly=True,
                                required=True,
                                copy=False,
                                tracking=True)
    delivery_number = fields.Char('Delivery Number',
                                  states={'draft': [('readonly', False)]},
                                  readonly=True,
                                  copy=False,
                                  tracking=True)
    notes = fields.Text('Notes')
    delivered_mass = fields.Float('Delivered Mass',
                                  digits='Unit of Measure',
                                  states={'draft': [('readonly', False)]},
                                  readonly=True,
                                  required=True,
                                  tracking=True)
    delivered_mass_uom_id = fields.Many2one(
        'uom.uom',
        'Mass Units',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    destination_partner_id = fields.Many2one(
        'res.partner',
        string='Destination',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    destination_address_id = fields.Many2one(
        'res.partner',
        string='Destination Address',
        domain="['|', "
        "('id', '=', destination_partner_id), "
        "('parent_id', '=', destination_partner_id)]",
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    sale_order_id = fields.Many2one(
        'sale.order',
        ondelete='restrict',
        domain="[('partner_id', '=', destination_partner_id)]",
        states={'draft': [('readonly', False)]},
        readonly=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=
        "[('is_agri_commodity', '=', True), ('categ_id.is_agri', '=', True)]",
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True)
    grading_id = fields.Many2one('agri.grading',
                                 string='Grading',
                                 ondelete='set null',
                                 states={'done': [('readonly', True)]},
                                 readonly=False)
    grading_product_qty = fields.Float(string='Grading Quantity',
                                       related='grading_id.product_qty')
    grading_line_ids = fields.One2many(related='grading_id.grading_line_ids',
                                       states={'done': [('readonly', True)]},
                                       readonly=False)
    transport_partner_id = fields.Many2one(
        'res.partner',
        string='Transport Provider',
        states={'draft': [('readonly', False)]},
        readonly=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('delivered', 'Delivered'),
                   ('done', 'Done')],
        string='State',
        default='draft',
        readonly=True,
        copy=False,
        tracking=True,
    )

    @api.depends('state')
    @api.onchange('state')
    def _compute_name(self):
        for delivery in self:
            if delivery.state == 'draft':
                delivery.name = 'Draft'
            elif not delivery.name or delivery.name == 'Draft':
                seq_no = self.env['ir.sequence'].next_by_code('agri.delivery')
                delivery.name = seq_no

    @api.depends('sale_order_id')
    @api.onchange('sale_order_id')
    def _compute_product(self):
        for delivery in self:
            products = delivery.sale_order_id.order_line.filtered(
                lambda order_line: order_line.product_id.is_agri)
            if len(products) > 0:
                delivery.product_id = products[0]

    @api.depends('product_id')
    @api.onchange('product_id')
    def _compute_delivered_mass_uom(self):
        for delivery in self:
            delivery.delivered_mass_uom_id = delivery.product_id.uom_id

    @api.onchange('product_id', 'delivered_mass', 'delivered_mass_uom_id')
    def _compute_grading(self):
        for delivery in self:
            if (delivery.product_id and delivery.delivered_mass_uom_id
                    and delivery.delivered_mass > 0):
                if (delivery.grading_id
                        and delivery.grading_id.product_tmpl_id.id !=
                        delivery.product_id.id):
                    delivery_data = delivery.copy_data({'grading_id': False})
                    delivery.grading_id.unlink()
                    delivery.write(delivery_data[0])
                if (not delivery.grading_id
                        and delivery.product_id.is_agri_commodity):
                    vals = {
                        'product_qty': delivery.delivered_mass,
                        'product_uom_id': delivery.delivered_mass_uom_id.id
                    }
                    if delivery.product_id.default_grading_id:
                        delivery.grading_id = delivery.product_id.default_grading_id.copy(
                            vals)
                    else:
                        vals.update(product_tmpl_id=delivery.product_id.id)
                        delivery.grading_id = self.env['agri.grading'].create(
                            vals)

    @api.depends('delivered_mass', 'delivered_mass_uom_id', 'grading_id')
    @api.onchange('delivered_mass', 'delivered_mass_uom_id')
    def _compute_product_qty(self):
        for delivery in self:
            if (delivery.grading_id and delivery.delivered_mass_uom_id
                    and delivery.delivered_mass > 0):
                delivery.grading_id.product_qty = delivery.delivered_mass
                delivery.grading_id.product_uom_id = delivery.delivered_mass_uom_id
                delivery.grading_product_qty = delivery.grading_id.product_qty
                line_commands = []
                for grading_line in delivery.grading_line_ids:
                    grading_line._compute_product_qty(
                        delivery.grading_id.product_qty)
                    line_commands += [(1, grading_line.id, {
                        'product_qty': grading_line.product_qty,
                        'price': grading_line.price,
                    })]
                delivery.grading_line_ids = line_commands
                delivery.grading_id.grading_line_ids = delivery.grading_line_ids

    def action_deliver(self):
        for delivery in self:
            delivery.state = 'delivered'
            delivery.message_subscribe([delivery.partner_id.id])

    def action_done(self):
        for delivery in self:
            delivery.state = 'done'

    def action_reset(self):
        for delivery in self:
            delivery.state = 'draft'
