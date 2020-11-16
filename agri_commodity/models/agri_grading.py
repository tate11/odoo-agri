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
        'Active', default=True,
        help="If the active field is set to False, it will allow you to hide the gradings without removing it.")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        check_company=True,
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=True)
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        check_company=True,
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu']),  '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If a product variant is defined the Grading is available only for this product.")
    grading_line_ids = fields.One2many('agri.grading.line', 'grading_id', 'Grading Lines', copy=True)
    byproduct_ids = fields.One2many('agri.grading.byproduct', 'grading_id', 'By-products', copy=True)
    product_qty = fields.Float(
        'Quantity', default=1.0,
        digits='Unit of Measure', required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_product_uom_id, required=True,
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control",
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of gradings.")
    company_id = fields.Many2one(
        'res.company', 'Company', index=True,
        default=lambda self: self.env.company)
    consumption = fields.Selection([
        ('strict', 'Strict'),
        ('flexible', 'Flexible')],
        help="Defines if you can consume more or less components than the quantity defined on the grading.",
        default='strict',
        string='Consumption'
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            for line in self.grading_line_ids:
                line.grading_product_template_attribute_value_ids = False

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
                        _("Grading line product %s should not be the same as grading product.") % grading.display_name)
                if grading.product_id and grading_line.grading_product_template_attribute_value_ids:
                    raise ValidationError(
                        _("Grading cannot concern product %s and have a line with attributes (%s) at the same time.")
                        % (grading.product_id.display_name, ", ".join(
                            [ptav.display_name for ptav in grading_line.grading_product_template_attribute_value_ids])))
                for ptav in grading_line.grading_product_template_attribute_value_ids:
                    if ptav.product_tmpl_id != grading.product_tmpl_id:
                        raise ValidationError(
                            _("The attribute value %s set on product %s does not match the Grading product %s.") %
                            (ptav.display_name, ptav.product_tmpl_id.display_name,
                             grading_line.parent_product_tmpl_id.display_name)
                        )

    @api.onchange('product_uom_id')
    def onchange_product_uom_id(self):
        res = {}
        if not self.product_uom_id or not self.product_tmpl_id:
            return
        if self.product_uom_id.category_id.id != self.product_tmpl_id.uom_id.category_id.id:
            self.product_uom_id = self.product_tmpl_id.uom_id.id
            res['warning'] = {'title': _('Warning'), 'message': _(
                'The Product Unit of Measure you chose has a different category than in the product form.')}
        return res

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            self.product_uom_id = self.product_tmpl_id.uom_id.id
            if self.product_id.product_tmpl_id != self.product_tmpl_id:
                self.product_id = False
            for line in self.grading_line_ids:
                line.grading_product_template_attribute_value_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for grading in res:
            if float_compare(grading.product_qty, 0, precision_rounding=grading.product_uom_id.rounding) <= 0:
                raise UserError(_('The quantity to produce must be positive!'))
        return res

    def write(self, values):
        res = super().write(values)
        for grading in self:
            if float_compare(grading.product_qty, 0, precision_rounding=grading.product_uom_id.rounding) <= 0:
                raise UserError(_('The quantity to produce must be positive!'))
        return res

    @api.model
    def name_create(self, name):
        # prevent to use string as product_tmpl_id
        if isinstance(name, str):
            raise UserError(_("You cannot create a new Grading from here."))
        return super(Grading, self).name_create(name)

    def name_get(self):
        return [
            (grading.id, '%s%s' % (grading.code and '%s: ' % grading.code or '', grading.product_tmpl_id.display_name))
            for grading in
            self]

    @api.model
    def _grading_find_domain(self, product_tmpl=None, product=None, picking_type=None, company_id=False):
        if product:
            if not product_tmpl:
                product_tmpl = product.product_tmpl_id
            domain = ['|', ('product_id', '=', product.id), '&', ('product_id', '=', False),
                      ('product_tmpl_id', '=', product_tmpl.id)]
        elif product_tmpl:
            domain = [('product_tmpl_id', '=', product_tmpl.id)]
        else:
            # neither product nor template, makes no sense to search
            raise UserError(_('You should provide either a product or a product template to search a grading'))
        if picking_type:
            domain += ['|', ('picking_type_id', '=', picking_type.id), ('picking_type_id', '=', False)]
        if company_id or self.env.context.get('company_id'):
            domain = domain + ['|', ('company_id', '=', False),
                               ('company_id', '=', company_id or self.env.context.get('company_id'))]
        # order to prioritize bom with product_id over the one without
        return domain

    @api.model
    def _grading_find(self, product_tmpl=None, product=None, picking_type=None, company_id=False):
        """ Finds BoM for particular product, picking and company """
        if product and product.type == 'service' or product_tmpl and product_tmpl.type == 'service':
            return False
        domain = self._grading_find_domain(product_tmpl=product_tmpl, product=product, picking_type=picking_type,
                                           company_id=company_id)
        if domain is False:
            return domain
        return self.search(domain, order='sequence, product_id', limit=1)

    def explode(self, product, quantity, picking_type=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        from collections import defaultdict

        graph = defaultdict(list)
        V = set()

        def check_cycle(v, visited, recStack, graph):
            visited[v] = True
            recStack[v] = True
            for neighbour in graph[v]:
                if visited[neighbour] == False:
                    if check_cycle(neighbour, visited, recStack, graph) == True:
                        return True
                elif recStack[neighbour] == True:
                    return True
            recStack[v] = False
            return False

        gradings_done = [(self, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
        lines_done = []
        V |= set([product.product_tmpl_id.id])

        grading_lines = [(grading_line, product, quantity, False) for grading_line in self.grading_line_ids]
        for grading_line in self.grading_line_ids:
            V |= set([grading_line.product_id.product_tmpl_id.id])
            graph[product.product_tmpl_id.id].append(grading_line.product_id.product_tmpl_id.id)
        while grading_lines:
            current_line, current_product, current_qty, parent_line = grading_lines[0]
            grading_lines = grading_lines[1:]

            if current_line._skip_grading_line(current_product):
                continue

            line_quantity = current_qty * current_line.product_qty
            grading = self._grading_find(product=current_line.product_id,
                                         picking_type=picking_type or self.picking_type_id,
                                         company_id=self.company_id.id)
            if grading:
                converted_line_quantity = current_line.product_uom_id._compute_quantity(
                    line_quantity / grading.product_qty,
                    grading.product_uom_id)
                grading_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in
                                 grading.grading_line_ids] + grading_lines
                for grading_line in grading.grading_line_ids:
                    graph[current_line.product_id.product_tmpl_id.id].append(grading_line.product_id.product_tmpl_id.id)
                    if grading_line.product_id.product_tmpl_id.id in V and check_cycle(
                        grading_line.product_id.product_tmpl_id.id, {key: False for key in V},
                        {key: False for key in V},
                        graph):
                        raise UserError(_(
                            'Recursion error!  A product with a grading should not have itself in its grading or child gradings!'))
                    V |= set([grading_line.product_id.product_tmpl_id.id])
                gradings_done.append((grading, {'qty': converted_line_quantity, 'product': current_product,
                                                'original_qty': quantity, 'parent_line': current_line}))
            else:
                # We round up here because the user expects that if he has to consume a little more, the whole UOM unit
                # should be consumed.
                rounding = current_line.product_uom_id.rounding
                line_quantity = float_round(line_quantity, precision_rounding=rounding, rounding_method='UP')
                lines_done.append((current_line,
                                   {'qty': line_quantity, 'product': current_product, 'original_qty': quantity,
                                    'parent_line': parent_line}))

        return gradings_done, lines_done

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

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    product_id = fields.Many2one('product.product', 'Component', required=True, check_company=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id',
                                      readonly=False)
    company_id = fields.Many2one(
        related='grading_id.company_id', store=True, index=True, readonly=True)
    product_qty = fields.Float(
        'Quantity', default=1.0,
        digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        default=_get_default_product_uom_id,
        required=True,
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control",
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    sequence = fields.Integer(
        'Sequence', default=1,
        help="Gives the sequence order when displaying.")
    grading_id = fields.Many2one(
        'agri.grading', 'Parent Grading',
        index=True, ondelete='cascade', required=True)
    parent_product_tmpl_id = fields.Many2one('product.template', 'Parent Product Template',
                                             related='grading_id.product_tmpl_id')
    possible_grading_product_template_attribute_value_ids = fields.Many2many('product.template.attribute.value',
                                                                             compute='_compute_possible_grading_product_template_attribute_value_ids')
    grading_product_template_attribute_value_ids = fields.Many2many(
        'product.template.attribute.value', string="Apply on Variants", ondelete='restrict',
        domain="[('id', 'in', possible_grading_product_template_attribute_value_ids)]",
        help="BOM Product Variants needed to apply this line.")
    child_grading_id = fields.Many2one(
        'agri.grading', 'Sub Grading', compute='_compute_child_grading_id')
    child_line_ids = fields.One2many(
        'agri.grading.line', string="Grading lines of the referred bom",
        compute='_compute_child_line_ids')
    attachments_count = fields.Integer('Attachments Count', compute='_compute_attachments_count')

    _sql_constraints = [
        ('bom_qty_zero', 'CHECK (product_qty>=0)', 'All product quantities must be greater or equal to 0.\n'
                                                   'Lines with 0 quantities can be used as optional lines. \n'
                                                   'You should install the mrp_byproduct module if you want to manage extra products on BoMs !'),
    ]

    @api.depends(
        'parent_product_tmpl_id.attribute_line_ids.value_ids',
        'parent_product_tmpl_id.attribute_line_ids.attribute_id.create_variant',
        'parent_product_tmpl_id.attribute_line_ids.product_template_value_ids.ptav_active',
    )
    def _compute_possible_grading_product_template_attribute_value_ids(self):
        for line in self:
            line.possible_grading_product_template_attribute_value_ids = line.parent_product_tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes().product_template_value_ids._only_active()

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
                '|',
                '&', ('res_model', '=', 'product.product'), ('res_id', '=', line.product_id.id),
                '&', ('res_model', '=', 'product.template'), ('res_id', '=', line.product_id.product_tmpl_id.id)])
            line.attachments_count = nbr_attach

    @api.depends('child_grading_id')
    def _compute_child_line_ids(self):
        """ If the BOM line refers to a BOM, return the ids of the child BOM lines """
        for line in self:
            line.child_line_ids = line.child_grading_id.grading_line_ids.ids or False

    @api.onchange('product_uom_id')
    def onchange_product_uom_id(self):
        res = {}
        if not self.product_uom_id or not self.product_id:
            return res
        if self.product_uom_id.category_id != self.product_id.uom_id.category_id:
            self.product_uom_id = self.product_id.uom_id.id
            res['warning'] = {'title': _('Warning'), 'message': _(
                'The Product Unit of Measure you chose has a different category than in the product form.')}
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'product_id' in values and 'product_uom_id' not in values:
                values['product_uom_id'] = self.env['product.product'].browse(values['product_id']).uom_id.id
        return super(GradingLine, self).create(vals_list)

    def _skip_grading_line(self, product):
        """ Control if a BoM line should be produced, can be inherited to add
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
                self.grading_product_template_attribute_value_ids.sorted('attribute_line_id'),
                lambda ptav: ptav.attribute_line_id):
                if not any([ptav in product.product_template_attribute_value_ids for ptav in iter_ptav]):
                    return True
        return False

    def action_see_attachments(self):
        domain = [
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', '=', self.product_id.id),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', self.product_id.product_tmpl_id.id)]
        attachment_view = self.env.ref('agri.agri_document_view_kanban')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'mrp.document',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Upload files to your product
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_company_id': %s}" % (
                'product.product', self.product_id.id, self.company_id.id)
        }


class ByProduct(models.Model):
    _name = 'agri.grading.byproduct'
    _description = 'Byproduct'
    _rec_name = "product_id"
    _check_company_auto = True

    product_id = fields.Many2one('product.product', 'By-product', required=True, check_company=True)
    company_id = fields.Many2one(related='grading_id.company_id', store=True, index=True, readonly=True)
    product_qty = fields.Float(
        'Quantity',
        default=1.0, digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    grading_id = fields.Many2one('agri.grading', 'BoM', ondelete='cascade')

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Changes UoM if product_id changes. """
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

    @api.onchange('product_uom_id')
    def onchange_uom(self):
        res = {}
        if self.product_uom_id and self.product_id and self.product_uom_id.category_id != self.product_id.uom_id.category_id:
            res['warning'] = {
                'title': _('Warning'),
                'message': _(
                    'The unit of measure you choose is in a different category than the product unit of measure.')
            }
            self.product_uom_id = self.product_id.uom_id.id
        return res
