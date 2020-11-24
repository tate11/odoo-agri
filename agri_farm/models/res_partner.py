from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    farm_version_id = fields.Many2one('agri.farm.version', 'Farm Version')
    farm_version_ids = fields.One2many(
        comodel_name='agri.farm.version',
        inverse_name='partner_id',
        string='Farm Versions',
    )
    farm_ids = fields.One2many(related='farm_version_id.farm_ids',
                               string='Farms')
    farm_count = fields.Integer(
        string='Farm Count',
        compute='_compute_farm_count',
        store=True,
    )

    @api.depends('farm_ids')
    def _compute_farm_count(self):
        for partner in self:
            partner.farm_count = len(partner.farm_version_id.farm_ids)

    def _create_farm_version(self):
        for partner in self:
            vals = {'partner_id': partner.id}
            if partner.company_id:
                vals.update(company_id=partner.company_id.id)
            farm_version = self.env['agri.farm.version'].create(vals)
            partner.write({'farm_version_id': farm_version.id})

    @api.model
    def create_missing_farm_versions(self):
        partner_without_farm_version = self.env['res.partner'].search([
            ('farm_version_id', '=', False)
        ])
        for partner in partner_without_farm_version:
            partner._create_farm_version()

    def _create_per_partner_farm_version(self):
        for partner in self:
            partner._create_farm_version()

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        partner.sudo()._create_per_partner_farm_version()
        return partner

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'company_id' in vals:
            farm_versions = self.env['agri.farm.version'].search([
                ('partner_id', '=', self.id)
            ])
            farm_versions.write({'company_id': vals['company_id']})
        return res
