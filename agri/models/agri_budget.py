from odoo import api, fields, models


class BudgetCategory(models.Model):
    _name = 'agri.budget.category'
    _description = 'Budget Category'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    uom_id = fields.Many2one('uom.uom',
                             'Unit of Measure',
                             required=True,
                             help="Unit of measure used for allocating costs.")
    type = fields.Selection(
        [('crop-sales', 'Crop Sales'), ('fruit-sales', 'Fruit Sales'),
         ('livestock-sales', 'Livestock Sales'),
         ('livestock-products', 'Livestock Products'),
         ('establishment', 'Establishment'), ('pre-harvest', 'Pre-harvest'),
         ('harvest', 'Harvest'), ('marketing', 'Marketing'),
         ('animal-feed', 'Animal Feed'), ('husbandry', 'Hubsandry'),
         ('indirect', 'Indirect')],
        string='Category Type',
        default='pre-harvest',
        required=True,
        help=
        'Budget category types determine how the income/expenses are allocated.\n'
        'Primary into incomes and expenses, but also in the life cycle of an.\n'
        'agricultural production system.')
    sale_ok = fields.Boolean('Can be Sold', default=True)
    purchase_ok = fields.Boolean('Can be Purchased', default=True)


class BudgetTemplate(models.Model):
    _name = 'agri.budget.template'
    _description = 'Budget Template'
    _order = 'name asc'

    name = fields.Char('Name', required=True)


class BudgetTemplateLine(models.Model):
    _name = 'agri.budget.template.line'
    _description = 'Budget Template'

    agri_budget_template_id = fields.Many2one(
        'agri.budget.template',
        'Template',
        required=True,
    )
    agri_budget_category_id = fields.Many2one(
        'agri.budget.category',
        'Category',
        required=True,
    )