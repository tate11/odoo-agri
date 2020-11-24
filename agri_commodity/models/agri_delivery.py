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
    delivered_mass_uom = fields.Many2one(
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
    grading_id = fields.Many2one(
        'agri.grading',
        string='Grading',
        domain="['|', ('delivery_id', '=', False), ('delivery_id', '=', id)]",
        states={'done': [('readonly', True)]},
        readonly=False)
    sale_order_id = fields.Many2one(
        'sale.order',
        ondelete='restrict',
        domain="[('partner_id', '=', destination_partner_id)]",
        states={'draft': [('readonly', False)]},
        readonly=True)
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

    def action_deliver(self):
        for deal in self:
            seq_no = self.env['ir.sequence'].next_by_code('agri.delivery')
            deal.state = 'delivered'
            deal.name = seq_no

    def action_done(self):
        for deal in self:
            deal.state = 'done'
