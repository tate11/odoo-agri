from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_compare

from itertools import groupby


class Grading(models.Model):
    """ Defines grading for a product or a product template """
    _name = 'agri.grading'
    _description = 'Grading'
    _inherit = ['mail.thread']
    _rec_name = 'product_tmpl_id'
    _order = "sequence"
    _check_company_auto = True

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    code = fields.Char('Reference')
    active = fields.Boolean(
        'Active',
        default=True,
        help=
        "If the active field is set to False, it will allow you to hide the gradings without removing it."
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product',
        check_company=True,
        domain="[('type', 'in', ['product', 'consu']), "
        "'|', "
        "('company_id', '=', False), "
        "('company_id', '=', company_id)]",
        required=True)
    product_id = fields.Many2one(
        'product.product',
        'Product Variant',
        check_company=True,
        domain="['&', "
        "('product_tmpl_id', '=', product_tmpl_id), "
        "('type', 'in', ['product', 'consu']),  "
        "'|', "
        "('company_id', '=', False), "
        "('company_id', '=', company_id)]",
        help=
        "If a product variant is defined the Grading is available only for this product."
    )
    grading_line_ids = fields.One2many('agri.grading.line',
                                       'grading_id',
                                       'Grading Lines',
                                       copy=True)
    byproduct_ids = fields.One2many('agri.grading.byproduct',
                                    'grading_id',
                                    'By-products',
                                    copy=True)
    product_qty = fields.Float('Quantity',
                               default=1.0,
                               digits='Unit of Measure',
                               required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id)
    price = fields.Monetary('Price',
                            compute='_compute_grading_lines',
                            digits='Product Price')
    product_uom_id = fields.Many2one(
        'uom.uom',
        'Unit of Measure',
        default=_get_default_product_uom_id,
        required=True,
        help=
        "Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control",
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    sequence = fields.Integer(
        'Sequence',
        help="Gives the sequence order when displaying a list of gradings.")
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 index=True,
                                 default=lambda self: self.env.company)
    consumption = fields.Selection(
        [('strict', 'Strict'), ('flexible', 'Flexible')],
        help=
        "Defines if you can consume more or less components than the quantity defined on the grading.",
        default='strict',
        string='Consumption')

    @api.constrains('product_qty')
    def _check_product_qty(self):
        for grading in self:
            total_percent = 0.0
            for line in grading.grading_line_ids:
                total_percent += line.percent
            if total_percent < 0 or total_percent > 100:
                raise ValidationError(_('Total percent must not exceed 100'))

    @api.onchange('product_id')
    def _compute_product_id(self):
        for grading in self:
            if grading.product_id:
                for line in grading.grading_line_ids:
                    line.grading_product_template_attribute_value_ids = False

    @api.onchange('product_qty')
    def _compute_product_qty(self):
        for grading in self:
            grading.grading_line_ids._compute_product_qty()

    @api.constrains('product_id', 'product_tmpl_id', 'grading_line_ids')
    def _check_grading_lines(self):
        for grading in self:
            for grading_line in grading.grading_line_ids:
                if grading.product_id:
                    same_product = grading.product_id == grading_line.product_id
                else:
                    same_product = grading.product_tmpl_id == grading_line.product_id.product_tmpl_id
                if same_product:
                    raise ValidationError(
                        _("Grading line product %s should not be the same as grading product."
                          ) % grading.display_name)
                if grading.product_id and grading_line.grading_product_template_attribute_value_ids:
                    raise ValidationError(
                        _("Grading cannot concern product %s and have a line with attributes (%s) at the same time."
                          ) % (grading.product_id.display_name, ", ".join([
                              ptav.display_name for ptav in grading_line.
                              grading_product_template_attribute_value_ids
                          ])))
                for ptav in grading_line.grading_product_template_attribute_value_ids:
                    if ptav.product_tmpl_id != grading.product_tmpl_id:
                        raise ValidationError(
                            _("The attribute value %s set on product %s does not match the Grading product %s."
                              ) %
                            (ptav.display_name,
                             ptav.product_tmpl_id.display_name, grading_line.
                             grading_product_tmpl_id.display_name))

    @api.depends('grading_line_ids', 'grading_line_ids.price')
    @api.onchange('grading_line_ids', 'grading_line_ids.price')
    def _compute_grading_lines(self):
        for grading in self:
            grading.price = sum(grading.grading_line_ids.mapped('price'))

    @api.onchange('product_uom_id')
    def _compute_product_uom_id(self):
        res = {}
        for grading in self:
            if not grading.product_uom_id or not grading.product_tmpl_id:
                return
            if (grading.product_uom_id.category_id.id !=
                    grading.product_tmpl_id.uom_id.category_id.id):
                grading.product_uom_id = grading.product_tmpl_id.uom_id.id
                res['warning'] = {
                    'title':
                    _('Warning'),
                    'message':
                    _('The Product Unit of Measure you chose has a different '
                      'category than in the product form.')
                }
        return res

    @api.onchange('product_tmpl_id')
    def _compute_product_tmpl_id(self):
        for grading in self:
            if grading.product_tmpl_id:
                grading.product_uom_id = self.product_tmpl_id.uom_id.id
                if grading.product_id.product_tmpl_id != grading.product_tmpl_id:
                    grading.product_id = False
                for line in grading.grading_line_ids:
                    line.grading_product_template_attribute_value_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for grading in res:
            if float_compare(
                    grading.product_qty,
                    0,
                    precision_rounding=grading.product_uom_id.rounding) <= 0:
                raise UserError(_('The quantity to produce must be positive!'))
        return res

    def write(self, values):
        res = super().write(values)
        for grading in self:
            if float_compare(
                    grading.product_qty,
                    0,
                    precision_rounding=grading.product_uom_id.rounding) <= 0:
                raise UserError(_('The quantity to produce must be positive!'))
        return res

    @api.model
    def name_create(self, name):
        # prevent to use string as product_tmpl_id
        if isinstance(name, str):
            raise UserError(_("You cannot create a new Grading from here."))
        return super(Grading, self).name_create(name)

    def name_get(self):
        return [(grading.id,
                 '%s%s' % (grading.code and '%s: ' % grading.code
                           or '', grading.product_tmpl_id.display_name))
                for grading in self]

    @api.model
    def _grading_find_domain(self,
                             product_tmpl=None,
                             product=None,
                             picking_type=None,
                             company_id=False):
        if product:
            if not product_tmpl:
                product_tmpl = product.product_tmpl_id
            domain = [
                '|', ('product_id', '=', product.id), '&',
                ('product_id', '=', False),
                ('product_tmpl_id', '=', product_tmpl.id)
            ]
        elif product_tmpl:
            domain = [('product_tmpl_id', '=', product_tmpl.id)]
        else:
            # neither product nor template, makes no sense to search
            raise UserError(
                _('You should provide either a product or a product template to search a grading'
                  ))
        if picking_type:
            domain += [
                '|', ('picking_type_id', '=', picking_type.id),
                ('picking_type_id', '=', False)
            ]
        if company_id or self.env.context.get('company_id'):
            domain = domain + [
                '|', ('company_id', '=', False),
                ('company_id', '=', company_id
                 or self.env.context.get('company_id'))
            ]
        # order to prioritize bom with product_id over the one without
        return domain

    @api.model
    def _grading_find(self,
                      product_tmpl=None,
                      product=None,
                      picking_type=None,
                      company_id=False):
        """ Finds BoM for particular product, picking and company """
        if (product and product.type == 'service'
                or product_tmpl and product_tmpl.type == 'service'):
            return False
        domain = self._grading_find_domain(product_tmpl=product_tmpl,
                                           product=product,
                                           picking_type=picking_type,
                                           company_id=company_id)
        if domain is False:
            return domain
        return self.search(domain, order='sequence, product_id', limit=1)

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Gradings'),
            'template': '/agri_commodity/static/xls/agri_grading.xls'
        }]


class GradingLine(models.Model):
    _name = 'agri.grading.line'
    _order = "sequence, id"
    _rec_name = "product_id"
    _description = 'Grading Line'
    _check_company_auto = True

    grading_id = fields.Many2one('agri.grading',
                                 'Grading',
                                 index=True,
                                 ondelete='cascade',
                                 required=True)
    grading_product_tmpl_id = fields.Many2one(
        'product.template',
        'Grading Product Template',
        related='grading_id.product_tmpl_id')
    grading_product_qty = fields.Float('Grading Quantity',
                                       related='grading_id.product_qty')
    grading_product_tmpl_categ_id = fields.Many2one(
        related='grading_product_tmpl_id.categ_id',
        string='Grading Product Template Category')
    product_id = fields.Many2one(
        'product.product',
        'Component',
        domain="[('product_tmpl_id', '!=', False), "
        "('product_tmpl_id', '!=', grading_product_tmpl_id), "
        "('product_tmpl_id.categ_id', '=', grading_product_tmpl_categ_id)]",
        required=True,
        check_company=True)
    product_tmpl_id = fields.Many2one('product.template',
                                      'Product Template',
                                      related='product_id.product_tmpl_id',
                                      readonly=False)
    company_id = fields.Many2one(related='grading_id.company_id',
                                 store=True,
                                 index=True,
                                 readonly=True)
    product_qty = fields.Float('Quantity',
                               compute='_compute_product_qty',
                               digits='Product Unit of Measure',
                               store=True)
    product_uom_id = fields.Many2one(
        'uom.uom',
        'Unit',
        required=True,
        help=
        "Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control",
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    currency_id = fields.Many2one(related='grading_id.currency_id', store=True)
    # price: total price, context dependent (partner, pricelist, quantity)
    unit_price = fields.Monetary('Unit Price',
                                 compute='_compute_product_qty',
                                 digits='Product Price',
                                 store=True)
    price = fields.Monetary('Price',
                            compute='_compute_product_qty',
                            digits='Product Price',
                            store=True)
    percent = fields.Float('Percent',
                           default=0.0,
                           digits=(3, 2),
                           required=True)
    sequence = fields.Integer('Sequence',
                              default=1,
                              help="Gives the sequence order when displaying.")
    possible_grading_product_template_attribute_value_ids = fields.Many2many(
        'product.template.attribute.value',
        compute='_compute_possible_grading_product_template_attribute_value_ids'
    )
    grading_product_template_attribute_value_ids = fields.Many2many(
        'product.template.attribute.value',
        string="Applicable Variants",
        ondelete='restrict',
        domain=
        "[('id', 'in', possible_grading_product_template_attribute_value_ids)]",
        help="BOM Product Variants needed to apply this line.")
    child_grading_id = fields.Many2one('agri.grading',
                                       'Sub Grading',
                                       compute='_compute_child_grading_id')
    child_line_ids = fields.One2many(
        'agri.grading.line',
        string="Grading lines of the referred grading",
        compute='_compute_child_line_ids')
    attachments_count = fields.Integer('Attachments Count',
                                       compute='_compute_attachments_count')

    _sql_constraints = [
        ('grading_qty_zero', 'CHECK (product_qty>=0)',
         'All product quantities must be greater or equal to 0.\n'
         'Lines with 0 quantities can be used as optional lines. \n'
         'You should install the mrp_byproduct module if you want to manage extra products on gradings !'
         ),
    ]

    @api.constrains('percent')
    def _check_percent(self):
        for line in self:
            if line.percent < 0 or line.percent > 100:
                raise ValidationError(_('Percent must be from 0 to 100'))

    @api.depends(
        'grading_product_tmpl_id.attribute_line_ids.value_ids',
        'grading_product_tmpl_id.attribute_line_ids.attribute_id.create_variant',
        'grading_product_tmpl_id.attribute_line_ids.product_template_value_ids.ptav_active',
    )
    def _compute_possible_grading_product_template_attribute_value_ids(self):
        for line in self:
            line.possible_grading_product_template_attribute_value_ids = line.grading_product_tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes(
            ).product_template_value_ids._only_active()

    @api.depends('product_id', 'grading_id')
    def _compute_child_grading_id(self):
        for line in self:
            if not line.product_id:
                line.child_grading_id = False
            else:
                line.child_grading_id = self.env['agri.grading']._grading_find(
                    product_tmpl=line.product_id.product_tmpl_id,
                    product=line.product_id)

    @api.depends('product_id')
    def _compute_attachments_count(self):
        for line in self:
            nbr_attach = self.env['agri.document'].search_count([
                '|', '&', ('res_model', '=', 'product.product'),
                ('res_id', '=', line.product_id.id), '&',
                ('res_model', '=', 'product.template'),
                ('res_id', '=', line.product_id.product_tmpl_id.id)
            ])
            line.attachments_count = nbr_attach

    @api.depends('child_grading_id')
    def _compute_child_line_ids(self):
        """ If the BOM line refers to a BOM, return the ids of the child BOM lines """
        for line in self:
            line.child_line_ids = line.child_grading_id.grading_line_ids.ids or False

    @api.onchange('product_uom_id')
    def _compute_product_uom_id(self):
        res = {}
        for line in self:
            if not line.product_uom_id or not line.product_id:
                return res
            if line.product_uom_id.category_id != line.product_id.uom_id.category_id:
                line.product_uom_id = line.product_id.uom_id.id
                res['warning'] = {
                    'title':
                    _('Warning'),
                    'message':
                    _('The Product Unit of Measure you chose has a different '
                      'category than in the product form.')
                }
        return res

    @api.depends('grading_product_qty', 'product_uom_id', 'percent')
    def _compute_product_qty(self, grading_product_qty=1.0):
        for line in self:
            line.product_qty = (line.grading_id.product_qty if line.grading_id
                                else grading_product_qty) * line.percent / 100.0
            line.unit_price = line.product_id.uom_id._compute_price(
                    line.product_id.with_context(
                        force_company=line.company_id.id).list_price,
                    line.product_uom_id) if line.product_id else 0.0
            line.price = line.unit_price * line.product_qty
        self.grading_id._compute_grading_lines()

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'product_id' in values and 'product_uom_id' not in values:
                values['product_uom_id'] = self.env['product.product'].browse(
                    values['product_id']).uom_id.id
        return super(GradingLine, self).create(vals_list)

    def _skip_grading_line(self, product):
        """ Control if a grading line should be produced, can be inherited to add
        custom control. It currently checks that all variant values are in the
        product.

        If multiple values are encoded for the same attribute line, only one of
        them has to be found on the variant.
        """
        self.ensure_one()
        if product._name == 'product.template':
            return False
        if self.grading_product_template_attribute_value_ids:
            for ptal, iter_ptav in groupby(
                    self.grading_product_template_attribute_value_ids.sorted(
                        'attribute_line_id'),
                    lambda ptav: ptav.attribute_line_id):
                if not any([
                        ptav in product.product_template_attribute_value_ids
                        for ptav in iter_ptav
                ]):
                    return True
        return False

    def action_see_attachments(self):
        domain = [
            '|', '&', ('res_model', '=', 'product.product'),
            ('res_id', '=', self.product_id.id), '&',
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.product_id.product_tmpl_id.id)
        ]
        attachment_view = self.env.ref('agri.agri_document_view_kanban')
        return {
            'name':
            _('Attachments'),
            'domain':
            domain,
            'res_model':
            'mrp.document',
            'type':
            'ir.actions.act_window',
            'view_id':
            attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode':
            'kanban,tree,form',
            'help':
            _('''<p class="o_view_nocontent_smiling_face">
                        Upload files to your product
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit':
            80,
            'context':
            "{'default_res_model': '%s','default_res_id': %d, 'default_company_id': %s}"
            % ('product.product', self.product_id.id, self.company_id.id)
        }


class ByProduct(models.Model):
    _name = 'agri.grading.byproduct'
    _description = 'Byproduct'
    _rec_name = "product_id"
    _check_company_auto = True

    product_id = fields.Many2one('product.product',
                                 'By-product',
                                 required=True,
                                 check_company=True)
    company_id = fields.Many2one(related='grading_id.company_id',
                                 store=True,
                                 index=True,
                                 readonly=True)
    product_qty = fields.Float('Quantity',
                               default=1.0,
                               digits='Product Unit of Measure',
                               required=True)
    product_uom_id = fields.Many2one('uom.uom',
                                     'Unit of Measure',
                                     required=True)
    grading_id = fields.Many2one('agri.grading', 'Grading', ondelete='cascade')

    @api.onchange('product_id')
    def _compute_product_id(self):
        """ Changes UoM if product_id changes. """
        for byproduct in self:
            byproduct.product_uom_id = byproduct.product_id.uom_id.id if byproduct.product_id else False

    @api.onchange('product_uom_id')
    def _compute_uom(self):
        res = {}
        for byproduct in self:
            if (byproduct.product_uom_id and byproduct.product_id
                    and byproduct.product_uom_id.category_id !=
                    byproduct.product_id.uom_id.category_id):
                res['warning'] = {
                    'title':
                    _('Warning'),
                    'message':
                    _('The unit of measure you choose is in a different '
                      'category than the product unit of measure.')
                }
                byproduct.product_uom_id = byproduct.product_id.uom_id.id
        return res
