from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    farm_parcel_id = fields.Many2one('agri.farm.parcel', 'Parcel')
    farm_parcel_ids = fields.One2many(
        comodel_name='agri.farm.parcel',
        inverse_name='partner_id',
        string='Parcels',
    )
    farm_ids = fields.One2many(related='farm_parcel_id.farm_ids',
                               string='Farms')
    farm_count = fields.Integer(
        string='Farm Count',
        compute='_compute_farm_count',
        store=True,
    )

    @api.depends('farm_ids')
    def _compute_farm_count(self):
        for partner in self:
            partner.farm_count = len(partner.farmland_id.farm_ids)

    def _create_farm_pacel(self):
        for partner in self:
            farmland_id = self.env['agri.farm_parcel'].create({
                'partner_id':
                partner.id,
            })

            partner.write({'farm_parcel_id': farmland_id.id})

    @api.model
    def create_missing_farm_parcel(self):
        partner_without_farmland = self.env['res.partner'].search([
            ('farm_parcel_id', '=', False)
        ])
        for partner in partner_without_farmland:
            partner._create_farmland()

    def _create_per_partner_farm_parcel(self):
        for partner in self:
            partner._create_farm_parcel()

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        partner.sudo()._create_per_partner_farm_parcel()
        return partner
