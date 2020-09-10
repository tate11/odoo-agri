from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FarmField(models.Model):
    _name = 'agri.farm.field'
    _description = 'Field'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Name', required=True, tracking=True)
    area_ha = fields.Float('Hectares', digits='Hectare', tracking=True)
    boundary = fields.GeoPolygon('Boundary', srid=4326, gist_index=True)
    has_boundary = fields.Boolean('Has Boundary',
                                  computed='_compute_has_boundary',
                                  default=False)
    established_date = fields.Date('Established Date', tracking=True)
    farm_id = fields.Many2one('agri.farm',
                              'Farm',
                              ondelete='cascade',
                              required=True)

    crop_potential_id = fields.Many2one('agri.crop.potential',
                                        'Crop Potential',
                                        tracking=True)
    soil_effective_depth_id = fields.Many2one('agri.soil.effective.depth',
                                              'Effective Depth',
                                              tracking=True)
    irrigated = fields.Boolean('Irrigated', default=False, tracking=True)
    irrigation_type_id = fields.Many2one('agri.irrigation.type',
                                         'Irrigation Type',
                                         tracking=True)
    land_use_id = fields.Many2one('agri.land.use',
                                  'Land Use',
                                  required=True,
                                  tracking=True)
    soil_texture_id = fields.Many2one('agri.soil.texture',
                                      'Soil Texture',
                                      tracking=True)
    terrain_id = fields.Many2one('agri.terrain', 'Terrain', tracking=True)
    water_source_id = fields.Many2one('agri.water.source',
                                      'Water Source',
                                      tracking=True)

    @api.onchange('boundary')
    def _compute_has_boundary(self):
        for field in self:
            field.has_boundary = True if field.boundary else False

    @api.constrains('name')
    def constrains_name(self):
        domain = [('farm_id', '=', self.farm_id.id), ('active', '=', True),
                  ('name', 'ilike', self.name)]
        if self.id:
            domain.append(('id', '!=', self.id))
        field = self.env['agri.field'].search(domain, limit=1)
        if field:
            raise ValidationError(_('Duplicate Field name'))

    @api.onchange('irrigation_type_id', 'land_use_id')
    def onchange_irrigated(self):
        self.irrigated = True if (self.land_use_id
                                  and self.land_use_id.irrigated
                                  ) or self.irrigation_type_id else False

    def name_get(self):
        return [(field.id, "{} ({:.3f} ha)".format(field.name, field.area_ha))
                for field in self]


class FarmParcel(models.Model):
    _name = 'agri.farm.parcel'
    _description = 'Parcel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'

    name = fields.Char('Name', required=True)
    short_name = fields.Char('Short Name', required=True)
    code = fields.Char('Code', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    area_ha = fields.Float('Hectares', digits='Hectare', tracking=True)
    boundary = fields.GeoPolygon('Boundary', srid=4326, gist_index=True)
    has_boundary = fields.Boolean('Has Boundary',
                                  computed='_compute_has_boundary',
                                  default=False)
    farm_id = fields.Many2one('agri.farm',
                              'Farm',
                              ondelete='cascade',
                              required=True)
    farm_land_use_ids = fields.One2many(comodel_name='agri.farm.land.use',
                                        inverse_name='farm_parcel_id',
                                        string='Land Uses',
                                        copy=True)

    @api.onchange('boundary')
    def _compute_has_boundary(self):
        for land in self:
            land.has_boundary = True if land.boundary else False

    @api.constrains('code')
    def constrains_code(self):
        domain = [('farm_id', '=', self.farm_id.id),
                  ('code', 'ilike', self.code)]
        if self.id:
            domain.append(('id', '!=', self.id))
        parcel = self.env['agri.farm.parcel'].search(domain, limit=1)
        if parcel:
            raise ValidationError(_('Duplicate Parcel'))

    def name_get(self):
        return [(parcel.id, "{} ({:.3f} ha)".format(parcel.name,
                                                    parcel.area_ha))
                for parcel in self]


class FarmLandUse(models.Model):
    _name = 'agri.farm.land.use'
    _description = 'Land Use'
    _order = 'area_ha desc'

    land_use_id = fields.Many2one('agri.land.use',
                                  'Land Use',
                                  ondelete='cascade',
                                  required=True)
    area_ha = fields.Float('Hectares', digits='Hectare', required=True)


class FarmVersion(models.Model):
    _name = 'agri.farm.version'
    _description = 'Farm Version'
    _order = 'date DESC'
    _check_company_auto = True

    name = fields.Char('Name',
                       computed='_compute_name',
                       readonly=True,
                       stored=True)
    date = fields.Date('Date',
                       default=fields.Date.context_today,
                       required=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade')
    company_id = fields.Many2one(related='partner_id.company_id',
                                 index=True,
                                 readonly=True,
                                 store=True)
    parent_farmland_id = fields.Many2one('agri.farmland', 'Parent Farmland')
    child_farmland_ids = fields.Many2many('agri.farmland',
                                          'agri_farmland_rel',
                                          'farmland_id',
                                          'child_id',
                                          string='Child Farmlands')
    farm_ids = fields.One2many(comodel_name='agri.farm',
                               inverse_name='farmland_id',
                               string='Farms',
                               copy=True)

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


class Farm(models.Model):
    _name = 'agri.farm'
    _description = 'Farm'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Name', required=True)
    area_ha = fields.Float('Hectares', digits='Hectare')
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

    @api.onchange('boundary')
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
            raise ValidationError(_('Duplicate Farm name'))

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.farmland_id = self.partner_id.farmland_id

    def name_get(self):
        return [(farm.id, "{} ({:.3f} ha)".format(farm.name, farm.area_ha))
                for farm in self]
