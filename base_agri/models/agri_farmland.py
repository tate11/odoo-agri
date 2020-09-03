from odoo import api, fields, models
from odoo.tools.misc import format_date


class AgriFarmland(models.Model):
    _name = 'agri.farmland'
    _description = 'Farmlands'
    _order = 'date DESC'

    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 check_company=True)
    name = fields.Char('Name',
                       computed='_compute_name',
                       readonly=True,
                       stored=True)
    date = fields.Date('Date',
                       default=fields.Date.context_today,
                       required=True)
    parent_farmland_id = fields.Many2one('agri.farmland', 'Parent Farmland')
    child_farmland_ids = fields.Many2many('agri.farmland',
                                          'agri_farmland_rel',
                                          'farmland_id',
                                          'child_id',
                                          string='Child Farmlands')
    farm_ids = fields.Many2one('agri.farm', 'Farms', copy=True)

    @api.depends('date')
    def _compute_name(self):
        for farmland in self:
            farmland.name = 'Farmland as of {}'.format(
                format_date(self.env, farmland.date))

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, parent_farmland_id=self)
        farmland = super(AgriFarmland, self).copy(default=default)
        self.write({'child_farmland_ids': [(4, [farmland.id])]})
        return farmland
