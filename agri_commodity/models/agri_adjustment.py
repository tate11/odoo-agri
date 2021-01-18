import math
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero


class Adjustment(models.Model):
    _name = 'agri.adjustment'
    _description = 'Adjustment'
    _order = 'name asc, create_date asc'

    name = fields.Char(string='Name', required=True)
    adjustment_type = fields.Selection(selection=[('deduction', 'Deduction'),
                                                  ('incentive', 'Incentive')],
                                       string='Type',
                                       required=True)
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 index=True,
                                 default=lambda self: self.env.company)
    model_id = fields.Many2one('ir.model',
                               string='On Model',
                               required=True,
                               ondelete='cascade')
    model_name = fields.Char('Model Name',
                             related='model_id.model',
                             store=True)
    product_id = fields.Many2one('product.product',
                                 string='Adjustment Product',
                                 ondelete='cascade')
    filter_partner_id = fields.Many2one('res.partner',
                                        string='Filtered Partner',
                                        ondelete='cascade')
    filter_product_tmpl_id = fields.Many2one('product.template',
                                             string='Filtered Product',
                                             ondelete='cascade')
    filter_start_date = fields.Date('Filtered Start Date')
    filter_end_date = fields.Date('Filtered End Date')
    condition_ids = fields.One2many(comodel_name='agri.adjustment.condition',
                                    inverse_name='adjustment_id',
                                    string='Adjustment Conditions',
                                    copy=True)
    modifier_ids = fields.One2many(comodel_name='agri.adjustment.modifier',
                                   inverse_name='adjustment_id',
                                   string='Adjustment Modifiers',
                                   copy=True)

    def _eval_conditions(self, model=None):
        for condition in self.condition_ids:
            if not self.condition_ids._eval_condition(model):
                return False
        return True

    def _compute_amount(self, model=None):
        eval_str = ''
        for adjustment in self:
            if model and model._name == adjustment.model_name:
                for modifier in adjustment.modifier_ids:
                    if ' ' in eval_str:
                        eval_str = _('(%s)') % (eval_str, )
                    if len(eval_str):
                        eval_str += _(' %s %s') % (
                            modifier.arithmetic_operator,
                            modifier._compute_amount(model))
                    else:
                        eval_str += _('%s') % (
                            modifier._compute_amount(model), )
        return eval(eval_str) if len(eval_str) else 0.0


class AdjustmentOperator(models.Model):
    _name = 'agri.adjustment.operator'
    _description = 'Adjustment Operator'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence', required=True)
    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Symbol', required=True)
    operator_type = fields.Selection(selection=[('general', 'General'),
                                                ('numeric', 'Numeric')],
                                     required=True)


class AdjustmentCondition(models.Model):
    _name = 'agri.adjustment.condition'
    _description = 'Adjustment Condition'
    _order = 'create_date asc'

    adjustment_id = fields.Many2one('agri.adjustment',
                                    string='Adjustment',
                                    required=True)
    name = fields.Char(string='Name', required=True)
    model_id = fields.Many2one(related='adjustment_id.model_id')
    model_field = fields.Many2one(
        'ir.model.fields',
        string='Field',
        domain=
        "[('model_id', '=', model_id), ('ttype', 'not in', ['one2many', 'many2many'])]"
    )
    model_field_ttype = fields.Selection(related='model_field.ttype')
    related_model_id = fields.Many2one('ir.model',
                                       string='Related Model',
                                       readonly=True)
    related_model_name = fields.Char(related='related_model_id.name',
                                     store=True)
    related_model_field = fields.Many2one(
        'ir.model.fields',
        string='Related Field',
        domain=
        "[('model_id', '=', related_model_id), ('ttype', 'not in', ['many2one', 'one2many', 'many2many'])]"
    )
    field_type = fields.Char(compute='_compute_field_type',
                             string='Field Type',
                             required=True)
    operator_id = fields.Many2one('agri.adjustment.operator',
                                  string='Operator',
                                  required=True)
    operator_symbol = fields.Char(related='operator_id.symbol')
    boolean_value = fields.Boolean('Boolean', digits=(3, 2))
    char_value = fields.Char('String', digits=(3, 2))
    date_value = fields.Date('Date', digits=(3, 2))
    date_from_value = fields.Date('Date From', digits=(3, 2))
    date_to_value = fields.Date('Date To', digits=(3, 2))
    number_value = fields.Float('Number', digits=(3, 2))
    number_from_value = fields.Float('Number From', digits=(3, 2))
    number_to_value = fields.Float('Number To', digits=(3, 2))

    @api.depends('field_type')
    @api.onchange('field_type')
    def _onchange_operators(self):
        self.operator_id = None
        return {
            'domain': {
                'operator_id':
                [] if self.field_type in ('date', 'float', 'integer',
                                          'monetary') else [('operator_type',
                                                             '=', 'general')]
            }
        }

    @api.depends('operator_id', 'field_type')
    @api.constrains('date_value', 'date_from_value', 'date_to_value')
    def _constrains_date(self):
        for condition in self:
            if condition.operator_id and condition.field_type == 'date':
                if (condition.operator_id.symbol == 'in'
                        and not condition.date_from_value
                        and not condition.date_to_value):
                    raise ValidationError(
                        _('Between condition needs a Date From and Date To.'))
                if (condition.operator_id.symbol != 'in'
                        and not condition.date_value):
                    raise ValidationError(_('Condition needs a Date.'))

    @api.depends('operator_id')
    @api.constrains('number_value', 'number_from_value', 'number_to_value')
    def _constrains_number(self):
        for condition in self:
            if condition.operator_id and condition.field_type in ('float',
                                                                  'integer',
                                                                  'monetary'):
                if (condition.operator_id.symbol == 'in'
                        and not condition.number_from_value
                        and not condition.number_to_value):
                    raise ValidationError(
                        _('Between condition needs a Value From and Value To.')
                    )
                if (condition.operator_id.symbol != 'in'
                        and not condition.number_value):
                    raise ValidationError(_('Condition needs a Value.'))

    @api.depends('operator_id', 'field_type')
    @api.onchange('operator_id', 'field_type')
    def _compute_value(self):
        for condition in self:
            # Reset based on field type
            if condition.field_type != 'boolean':
                condition.boolean_value = False
            if condition.field_type != 'char':
                condition.char_value = False
            if condition.field_type != 'date':
                condition.date_value = False
                condition.date_from_value = False
                condition.date_to_value = False
            if condition.field_type not in ('float', 'integer', 'monetary'):
                condition.number_value = False
                condition.number_from_value = False
                condition.number_to_value = False
            # Reset between operator
            if condition.operator_id.symbol == 'in':
                condition.date_value = False
                condition.number_value = False
            else:
                condition.date_from_value = False
                condition.date_to_value = False
                condition.number_from_value = False
                condition.number_to_value = False

    @api.depends('model_field')
    @api.onchange('model_field')
    def _compute_related_model(self):
        for condition in self:
            model = self.env['ir.model'].sudo().search(
                [('model', '=', condition.model_field.relation)], limit=1
            ) if condition.model_field and condition.model_field.ttype in [
                'many2one', 'one2many', 'many2many'
            ] else False
            if model:
                condition.related_model_id = model
                condition.related_model_field = False
            else:
                condition.related_model_id = False
                condition.related_model_field = False

    @api.depends('model_field', 'related_model_field')
    @api.onchange('model_field', 'related_model_field')
    def _compute_field_type(self):
        for condition in self:
            condition.field_type = (condition.related_model_field.ttype
                                    if condition.related_model_field else
                                    condition.model_field.ttype)

    def _eval_condition(self, model=None):
        self.ensure_one()
        model_value = model[
            self.model_field.name] if self.model_field and hasattr(
                model, self.model_field.name) else None
        model_value = model_value[
            self.related_model_field.
            name] if self.related_model_field and hasattr(
                model_value, self.related_model_field.name) else model_value
        if self.field_type == 'date':
            return (
                model_value >= self.date_from_value
                and model_value <= self.date_to_value
            ) if self.operator_id.symbol == 'in' else eval(
                _('%s %s %s') %
                (model_value, self.operator_id.symbol, self.date_value))
        if self.field_type in ('float', 'integer', 'monetary'):
            return (
                model_value >= self.number_from_value
                and model_value <= self.number_to_value
            ) if self.operator_id.symbol == 'in' else eval(
                _('%s %s %s') %
                (model_value, self.operator_id.symbol, self.number_value))
        return eval(
            _('%s %s %s') %
            (model_value, self.operator_id.symbol, self.boolean_value
             if self.field_type == 'boolean' else self.char_value))

    @api.model
    def create(self, vals):
        if self.related_model_field and not self.related_model_id:
            vals.update(
                {'related_model_id': self.related_model_field.model_id.id})
        return super(AdjustmentCondition, self).create(vals)

    def write(self, vals):
        if self.related_model_field and not self.related_model_id:
            vals.update(
                {'related_model_id': self.related_model_field.model_id.id})
        return super(AdjustmentCondition, self).write(vals)


class AdjustmentModifier(models.Model):
    _name = 'agri.adjustment.modifier'
    _description = 'Adjustment Modifier'
    _order = 'sequence asc'

    sequence = fields.Integer('Sequence', default=1)
    adjustment_id = fields.Many2one('agri.adjustment',
                                    string='Adjustment',
                                    required=True)
    name = fields.Char(string='Name', required=True)
    model_id = fields.Many2one(related='adjustment_id.model_id')
    model_field = fields.Many2one(
        'ir.model.fields',
        string='Field',
        domain=
        "[('model_id', '=', model_id), ('ttype', 'not in', ['one2many', 'many2many'])]"
    )
    model_field_ttype = fields.Selection(related='model_field.ttype')
    related_model_id = fields.Many2one('ir.model',
                                       string='Related Model',
                                       readonly=True)
    related_model_name = fields.Char(related='related_model_id.name',
                                     store=True)
    related_model_field = fields.Many2one(
        'ir.model.fields',
        string='Related Field',
        domain=
        "[('model_id', '=', related_model_id), ('ttype', 'in', ['float', 'integer', 'monetary'])]"
    )
    math_operator = fields.Selection(selection=[('abs', 'Abs'),
                                                ('floor', 'Floor'),
                                                ('ceil', 'Ceil')],
                                     string='Math Operator')
    arithmetic_operator = fields.Selection(selection=[('+', 'Plus'),
                                                      ('-', 'Minus'),
                                                      ('/', 'Divide'),
                                                      ('*', 'Times')],
                                           string='Arithmetic Operator',
                                           required=True)
    value_source = fields.Selection(selection=[('variable', 'Variable'),
                                               ('model', 'From Model'),
                                               ('product', 'From Product')],
                                    string='Value Source',
                                    default='variable',
                                    required=True)
    value = fields.Float('Variable', digits=(3, 2))

    @api.constrains('value_source')
    def _check_value_source(self):
        for modifier in self:
            if modifier.value_source == 'product' and not modifier.adjustment_id.product_id:
                raise ValidationError(
                    _('Adjustment Product must be set.'))

    @api.depends('value_source')
    @api.onchange('value_source')
    def _compute_value_source(self):
        for modifier in self:
            if modifier.value_source == 'variable':
                modifier.model_field = False
                modifier.related_model_id = False
                modifier.related_model_field = False
            else:
                modifier.value = 0.0

    @api.depends('model_field')
    @api.onchange('model_field')
    def _compute_related_model(self):
        for modifier in self:
            model = self.env['ir.model'].sudo().search(
                [('model', '=', modifier.model_field.relation)], limit=1
            ) if modifier.model_field and modifier.model_field.ttype in [
                'many2one', 'one2many', 'many2many'
            ] else False
            if model:
                modifier.related_model_id = model
                modifier.related_model_field = False
            else:
                modifier.related_model_id = False
                modifier.related_model_field = False

    def _eval_amount(self, model=None):
        return _(' %s %s') % (self.arithmetic_operator,
                              self._compute_amount(model))

    def _compute_amount(self, model=None):
        self.ensure_one()
        if self.value_source == 'model':
            model_value = model[
                self.model_field.name] if self.model_field and hasattr(
                    model, self.model_field.name) else None
            model_value = model_value[
                self.related_model_field.
                name] if self.related_model_field and hasattr(
                    model_value,
                    self.related_model_field.name) else model_value
            if self.math_operator:
                model_value = eval(
                    _('math.%s(%s)') % (self.math_operator, model_value))
            return model_value
        elif self.value_source == 'product':
            return self.adjustment_id.product_id.list_price
        return self.value

    @api.model
    def create(self, vals):
        if self.related_model_field and not self.related_model_id:
            vals.update(
                {'related_model_id': self.related_model_field.model_id.id})
        return super(AdjustmentModifier, self).create(vals)

    def write(self, vals):
        if self.related_model_field and not self.related_model_id:
            vals.update(
                {'related_model_id': self.related_model_field.model_id.id})
        return super(AdjustmentModifier, self).write(vals)
