from odoo import api, fields, models


class AgriFarmland(models.Model):
    _name = 'agri.farmland'
    _description = 'Farmland'
    _order = 'sequence DESC'

    company_id = fields.Many2one('res.company',
                                 'Company',
                                 default=lambda self: self.env.company,
                                 copy=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 copy=True)
    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=1)
    parent_plan_id = fields.Many2one('agri.plan', 'Parent Plan')
    child_plan_ids = fields.Many2many('agri.plan', 'agri_plan_rel', 'plan_id',
                                      'child_id')
    farm_ids = fields.Many2one('agri.farm', 'Farms', copy=True)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        sequence = self.sequence + 1
        name = default.get('name', 'Plan {}'.format(sequence))
        default.update({
            'name': name,
            'sequence': sequence,
            'parent_plan_id': self
        })
        plan = super(AgriFarmland, self).copy(default=default)
        self.write({'child_plan_ids': [(4, [plan.id])]})
        return plan
