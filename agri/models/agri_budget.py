from odoo import api, fields, models


class BudgetTemplate(models.Model):
    _name = 'agri.budget.template'
    _description = 'Budget Template'
    _order = 'name asc'

    name = fields.Char('Name', required=True)


class BudgetTemplateLine(models.Model):
    _name = 'agri.budget.template.line'
    _description = 'Budget Template'

    agri_budget_template_id = fields.Many2one('agri.budget.template',
                                              'Template',
                                              required=True)
    product_category_id = fields.Many2one('product.category',
                                          'Category',
                                          domain="[('is_agri', '=', True)]",
                                          required=True)
