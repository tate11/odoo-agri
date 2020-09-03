from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    farmland_id = fields.Many2one('agri.farmland', 'Farmland')
    farmland_ids = fields.One2many(
        comodel_name='agri.farmland',
        inverse_name='partner_id',
        string='Farmlands',
    )
    farm_ids = fields.Related('farmland_id.farm_ids', 'Farms')

    def _create_farmland(self):
        for partner in self:
            farmland_id = self.env['agri.farmland'].create({
                'partner_id':
                partner.id,
            })

            partner.write({'farmland_id': farmland_id.id})

    @api.model
    def create_missing_farmland(self):
        partner_without_farmland = self.env['res.partner'].search([
            ('farmland_id', '=', False)
        ])
        for partner in partner_without_farmland:
            partner._create_farmland()

    def _create_per_partner_farmland(self):
        for partner in self:
            partner._create_farmland()

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        partner.sudo()._create_per_partner_farmland()
        return partner
