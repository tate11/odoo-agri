from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AgriFarm(models.Model):
    _name = 'agri.farm'
    _description = 'Farms'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Name', required=True)
    area_ha = fields.Float('Hectares')
    boundary = fields.GeoPolygon('Boundary', srid=4326, gist_index=True)
    has_boundary = fields.Boolean('Has Boundary',
                                  computed='_compute_has_boundary',
                                  default=False)
    farmland_id = fields.Many2one('agri.farmland',
                                  'Farmland',
                                  ondelete='cascade',
                                  required=True,
                                  check_company=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 required=True,
                                 check_company=True)
    company_id = fields.Many2one(related='partner_id.company_id',
                                 index=True,
                                 readonly=True,
                                 store=True)
    field_ids = fields.One2many(comodel_name='agri.field',
                                inverse_name='farm_id',
                                string='Fields',
                                copy=True)
    land_ids = fields.One2many(comodel_name='agri.land',
                               inverse_name='farm_id',
                               string='Land',
                               copy=True)

    @api.depends('boundary')
    def _compute_has_boundary(self):
        for farm in self:
            farm.has_boundary = True if farm.boundary else False

    @api.constrains('name')
    def constrains_name(self):
        domain = [('farmland_id', '=', self.farmland_id.id),
                  ('active', '=', True), ('name', 'ilike', self.name)]
        if self.id:
            domain.append(('id', '!=', self.id))
        farm = self.env['agri.farm'].search(domain, limit=1)
        if farm:
            raise ValidationError('Duplicate Farm name')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.farmland_id = self.partner_id.farmland_id

    def name_get(self):
        return [(farm.id, "{} ({:.3f} ha)".format(farm.name, farm.area_ha))
                for farm in self]
