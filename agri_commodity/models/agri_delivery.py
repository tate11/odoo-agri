from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class Delivery(models.Model):
    _name = 'agri.delivery'
    _description = 'Delivery'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    name = fields.Char(string='Name', default='New', readonly=True, copy=False)
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
                                       copy=False,
                                       tracking=True)
    delivery_date = fields.Date(string='Delivery Date',
                                states={'draft': [('readonly', False)]},
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
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 domain="[('is_agri_commodity', '=', True), ('categ_id.is_agri', '=', True)]",
                                 states={'draft': [('readonly', False)]},
                                 readonly=True,
                                 required=True)
    grading_id = fields.Many2one(
        'agri.grading',
        string='Grading',
        ondelete='set null',
        states={'done': [('readonly', True)]},
        readonly=False)
    grading_product_qty = fields.Float(string='Grading Quantity',
                                       related='grading_id.product_qty')
    grading_line_ids = fields.One2many(related='grading_id.grading_line_ids',
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

    @api.depends('sale_order_id')
    @api.onchange('sale_order_id')
    def _compute_product(self):
        for line in self:
            products = line.sale_order_id.order_line.filtered(lambda order_line: order_line.product_id.is_agri)
            if len(products) > 0:
                line.product_id = products[0]

    @api.depends('product_id')
    @api.onchange('product_id')
    def _compute_delivered_mass_uom(self):
        for line in self:
            line.delivered_mass_uom_id = line.product_id.uom_id

    @api.onchange('product_id', 'delivered_mass', 'delivered_mass_uom_id')
    def _compute_grading(self):
        for line in self:
            if line.product_id and line.delivered_mass_uom_id and line.delivered_mass > 0:
                if (line.grading_id and line.grading_id.product_tmpl_id.id !=
                        line.product_id.id):
                    line_data = line.copy_data({'grading_id': False})
                    line.grading_id.unlink()
                    line.write(line_data[0])
                if (not line.grading_id and line.product_id.is_agri_commodity):
                    vals = {
                        'product_qty': line.delivered_mass,
                        'product_uom_id': line.delivered_mass_uom_id.id
                    }
                    if line.product_id.default_grading_id:
                        line.grading_id = line.product_id.default_grading_id.copy(
                            vals)
                    else:
                        vals.update(product_tmpl_id=line.product_id.id)
                        line.grading_id = self.env['agri.grading'].create(vals)

    @api.depends('delivered_mass', 'delivered_mass_uom_id', 'grading_id')
    @api.onchange('delivered_mass', 'delivered_mass_uom_id')
    def _compute_product_qty(self):
        for line in self:
            if line.grading_id and line.delivered_mass_uom_id and line.delivered_mass > 0:
                line.grading_id.product_qty = line.delivered_mass
                line.grading_id.product_uom_id = line.delivered_mass_uom_id
                line.grading_product_qty = line.grading_id.product_qty
                line_commands = []
                for grading_line in line.grading_line_ids:
                    grading_line._compute_product_qty(line.grading_id.product_qty)
                    line_commands += [(1, grading_line.id, {
                        'product_qty': grading_line.product_qty,
                        'price': grading_line.price,
                    })]
                line.grading_line_ids = line_commands
                line.grading_id.grading_line_ids = line.grading_line_ids

    def action_deliver(self):
        for delivery in self:
            seq_no = self.env['ir.sequence'].next_by_code('agri.delivery')
            delivery.state = 'delivered'
            delivery.name = seq_no
            delivery.message_subscribe([delivery.partner_id.id])

    def action_done(self):
        for delivery in self:
            delivery.state = 'done'
