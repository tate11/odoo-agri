from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class Farm(models.Model):
    _name = 'agri.farm'
    _description = 'Farm'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _check_company_auto = True

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 required=True,
                                 check_company=True)
    company_id = fields.Many2one('res.company',
                                 required=True,
                                 default=lambda self: self.env.company)
    area_uom_id = fields.Many2one(
        'uom.uom',
        'Area Unit',
        domain="[('name', 'in', ['ac', 'ha'])]",
        default=lambda self: self.env.ref('agri.agri_uom_ha'),
        required=True,
        tracking=True)
    area = fields.Float('Area', digits='Hectare', tracking=True)
    boundary = fields.GeoMultiPolygon('Boundary', srid=4326, gist_index=True)
    has_boundary = fields.Boolean('Has Boundary',
                                  compute='_compute_has_boundary',
                                  default=False)
    farm_field_ids = fields.One2many(comodel_name='agri.farm.field',
                                     inverse_name='farm_id',
                                     string='Fields',
                                     copy=True)
    farm_parcel_ids = fields.One2many(comodel_name='agri.farm.parcel',
                                      inverse_name='farm_id',
                                      string='Parcels',
                                      copy=True)
    farm_version_id = fields.Many2one('agri.farm.version',
                                      'Farm Version',
                                      ondelete='cascade',
                                      required=True,
                                      check_company=True)

    @api.onchange('boundary')
    def _compute_has_boundary(self):
        for farm in self:
            farm.has_boundary = True if farm.boundary else False

    @api.constrains('name')
    def _check_name(self):
        domain = [('farm_version_id', '=', self.farm_version_id.id),
                  ('active', '=', True), ('name', 'ilike', self.name)]
        if self.id:
            domain.append(('id', '!=', self.id))
        farm = self.env['agri.farm'].search(domain, limit=1)
        if farm:
            raise ValidationError(_('Duplicate Farm name'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for farm in self:
            farm.farm_version_id = farm.partner_id.farm_version_id if farm.partner_id else False

    def name_get(self):
        return [(farm.id, "{} ({:.3f} {})".format(farm.name, farm.area,
                                                  farm.area_uom_id.name))
                for farm in self]

    @api.model
    def create(self, vals):
        farm = super(Farm, self).create(vals)
        farm.message_subscribe([farm.partner_id.id])
        return farm

    def write(self, vals):
        res = super(Farm, self).write(vals)
        if 'partner_id' in vals:
            farm = self.browse(self.id)
            farm.message_unsubscribe([self.partner_id.id])
            farm.message_subscribe([farm.partner_id.id])
            for field in farm.farm_field_ids:
                field.message_unsubscribe([self.partner_id.id])
                field.message_subscribe([farm.partner_id.id])
                for crop in field.crop_ids:
                    crop.message_unsubscribe([self.partner_id.id])
                    crop.message_subscribe([farm.partner_id.id])
                    crop.zone_ids.message_unsubscribe([self.partner_id.id])
                    crop.zone_ids.message_subscribe([farm.partner_id.id])
            farm.farm_parcel_ids.message_unsubscribe([self.partner_id.id])
            farm.farm_parcel_ids.message_subscribe([farm.partner_id.id])
        return res


class FarmField(models.Model):
    _name = 'agri.farm.field'
    _description = 'Farm Field'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Name', required=True, tracking=True)
    area = fields.Float('Area', digits='Hectare', tracking=True)
    area_uom_id = fields.Many2one(related='farm_id.area_uom_id', store=True)
    boundary = fields.GeoMultiPolygon('Boundary', srid=4326, gist_index=True)
    has_boundary = fields.Boolean('Has Boundary',
                                  compute='_compute_has_boundary',
                                  default=False)
    farm_id = fields.Many2one('agri.farm',
                              'Farm',
                              ondelete='cascade',
                              required=True)
    farm_version_id = fields.Many2one(related='farm_id.farm_version_id',
                                      readonly=True)
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
    crop_ids = fields.One2many(comodel_name='agri.farm.field.crop',
                               inverse_name='field_id',
                               string='Crops',
                               copy=True)
    crop_count = fields.Integer(string='Crop Count',
                                compute='_compute_crops',
                                store=True)

    @api.onchange('boundary')
    def _compute_has_boundary(self):
        for field in self:
            field.has_boundary = True if field.boundary else False

    @api.depends('crop_ids')
    def _compute_crops(self):
        for field in self:
            field.crop_count = len(field.crop_ids)

    @api.constrains('name')
    def _check_name(self):
        for farm in self:
            domain = [('farm_id', '=', farm.farm_id.id), ('active', '=', True),
                      ('name', 'ilike', farm.name)]
            if farm.id:
                domain.append(('id', '!=', farm.id))
            field = self.env['agri.farm.field'].search(domain, limit=1)
            if field:
                raise ValidationError(_('Duplicate Field name'))

    @api.onchange('irrigation_type_id', 'land_use_id')
    def _onchange_irrigated(self):
        for field in self:
            field.irrigated = True if (field.land_use_id
                                       and field.land_use_id.irrigated
                                       ) or field.irrigation_type_id else False

    def name_get(self):
        return [(field.id, "{} ({:.3f} {})".format(field.name, field.area,
                                                   field.area_uom_id.name))
                for field in self]

    def _message_create(self, values_list):
        if not isinstance(values_list, (list)):
            values_list = [values_list]
        res = super(FarmField, self)._message_create(values_list)
        for values in values_list:
            log_values = {
                key: values[key]
                for key in values.keys()
                & {'tracking_value_ids', 'attachment_ids'}
            }
            body = (
                values.get('body') if 'body' in values
                and len(values.get('body')) else _('%s updated:') %
                (self._description, )).replace(
                    self._description,
                    _("%s <a href=# data-oe-model=%s data-oe-id=%d>%s</a>") %
                    (self._description, self._name, self.id, self.name))
            self.farm_id._message_log(**log_values, body=body)

    @api.model
    def create(self, vals):
        field = super(FarmField, self).create(vals)
        field.message_subscribe([field.farm_id.partner_id.id])
        return field


class FarmFieldCrop(models.Model):
    _name = 'agri.farm.field.crop'
    _description = 'Field Crop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'field_id, farm_id asc'
    _check_company_auto = True

    name = fields.Char('Name',
                       compute='_compute_name',
                       readonly=True,
                       stored=True)
    field_id = fields.Many2one('agri.farm.field',
                               string='Field',
                               states={'draft': [('readonly', False)]},
                               readonly=True,
                               required=True)
    farm_id = fields.Many2one(related='field_id.farm_id', store=True)
    product_category_id = fields.Many2one(
        'product.category',
        'Crop Category',
        domain=lambda self: [('parent_id', 'in', [
            self.env.ref('agri.product_category_crop').id,
            self.env.ref('agri.product_category_permanent_crop').id
        ])],
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        tracking=True)
    problem_ids = fields.One2many(comodel_name='agri.farm.field.crop.problem',
                                  inverse_name='crop_id',
                                  string='Problems',
                                  copy=True)
    problem_count = fields.Integer(string='Problem Count',
                                   compute='_compute_problems',
                                   store=True)
    zone_ids = fields.One2many(comodel_name='agri.farm.field.crop.zone',
                               inverse_name='crop_id',
                               string='Zones',
                               copy=True)
    zone_count = fields.Integer(string='Zone Count',
                                compute='_compute_zones',
                                store=True)
    planted_area = fields.Float('Planted Area',
                                compute='_compute_areas',
                                store=True,
                                tracking=True)
    emerged_area = fields.Float('Emerged Area',
                                compute='_compute_areas',
                                store=True,
                                tracking=True)
    established_date = fields.Date('Established Date',
                                   compute='_compute_dates',
                                   store=True,
                                   tracking=True)
    cleared_date = fields.Date('Cleared Date',
                               compute='_compute_dates',
                               store=True,
                               tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('planted', 'Planted'),
                                        ('emerged', 'Emerged'),
                                        ('harvested', 'Harvested')],
                             compute='_compute_state',
                             string='State',
                             copy=False,
                             store=True,
                             tracking=True)

    @api.depends('product_category_id', 'field_id')
    @api.onchange('product_category_id', 'field_id')
    def _compute_name(self):
        for crop in self:
            crop.name = _('%s on %s') % (crop.product_category_id.name,
                                         crop.field_id.name)

    @api.depends('problem_ids', 'problem_ids.state')
    def _compute_problems(self):
        for crop in self:
            crop.problem_count = len(
                crop.problem_ids.filtered(
                    lambda problem: problem.state == 'posted'))

    @api.depends('zone_ids')
    def _compute_zones(self):
        for crop in self:
            crop.zone_count = len(crop.zone_ids)

    @api.depends('zone_ids', 'zone_ids.planted_area', 'zone_ids.emerged_area',
                 'zone_ids.state')
    def _compute_areas(self):
        for crop in self:
            crop.planted_area = sum(crop.zone_ids.mapped('planted_area'))
            crop.emerged_area = sum(
                crop.zone_ids.filtered(lambda zone: zone.state in (
                    'emerged', 'harvested')).mapped('emerged_area'))

    @api.depends('zone_ids', 'zone_ids.planted_date',
                 'zone_ids.harvested_date')
    def _compute_dates(self):
        for crop in self:
            planted_zone = self.env['agri.farm.field.crop.zone'].search(
                [('crop_id', '=', crop.id)], limit=1, order='planted_date ASC')
            harvested_zone = self.env['agri.farm.field.crop.zone'].search(
                [('crop_id', '=', crop.id), ('harvested_date', '!=', False)],
                limit=1,
                order='harvested_date DESC')
            crop.established_date = planted_zone.planted_date if planted_zone else False
            crop.cleared_date = harvested_zone.harvested_date if harvested_zone else False

    @api.model
    def _has_zones_in_state(self, state):
        return len(self.zone_ids.filtered(lambda zone: zone.state == state))

    @api.depends('field_id', 'zone_ids.state')
    def _compute_state(self):
        for crop in self:
            if crop._has_zones_in_state('harvested'):
                crop.state = 'harvested'
            elif crop._has_zones_in_state('emerged'):
                crop.state = 'emerged'
            elif crop._has_zones_in_state('planted'):
                crop.state = 'planted'
            else:
                crop.state = 'draft'

    @api.constrains('established_date', 'cleared_date')
    def _check_established_cleared_date(self):
        for crop in self:
            domain = [('field_id', '=', crop.field_id.id), '|', '&',
                      ('established_date', '<=', crop.established_date),
                      ('cleared_date', '=', False)]
            if not crop.cleared_date:
                domain += ['&', ('established_date', '<=', crop.established_date),
                           ('cleared_date', '>=', crop.established_date)]
            else:
                domain += [
                    '|', '&',
                    ('established_date', '>=', crop.established_date),
                    ('established_date', '<=', crop.cleared_date), '&',
                    ('cleared_date', '>=', crop.established_date),
                    ('cleared_date', '<=', crop.cleared_date)
                ]
            if crop.id:
                domain = [('id', '!=', crop.id)] + domain
            dup_crop = self.env['agri.farm.field.crop'].search(domain, limit=1)
            if dup_crop:
                raise ValidationError(_('Crop overlaps existing Crop'))

    def _message_create(self, values_list):
        if not isinstance(values_list, (list)):
            values_list = [values_list]
        res = super(FarmFieldCrop, self)._message_create(values_list)
        for values in values_list:
            log_values = {
                key: values[key]
                for key in values.keys()
                & {'tracking_value_ids', 'attachment_ids'}
            }
            body = (
                values.get('body') if 'body' in values
                and len(values.get('body')) else _('%s updated:') %
                (self._description, )).replace(
                    self._description,
                    _("%s <a href=# data-oe-model=%s data-oe-id=%d>%s</a>") %
                    (self._description, self._name, self.id, self.name))
            self.field_id._message_log(**log_values, body=body)

    @api.model
    def create(self, vals):
        crop_vals = {
            key: vals[key]
            for key in self._fields.keys() if key in vals
        }
        crop = super(FarmFieldCrop, self).create(crop_vals)
        crop.message_subscribe([crop.farm_id.partner_id.id])
        if all(key in vals
               for key in ('planted_area', 'planted_date', 'product_id')):
            vals.update(crop_id=crop.id)
            self.env['agri.farm.field.crop.zone'].create(vals)
        return crop


class FarmFieldCropProblem(models.Model):
    _name = 'agri.farm.field.crop.problem'
    _description = 'Crop Problem'
    _order = 'name, create_date desc'

    name = fields.Char('Name',
                       compute='_compute_name',
                       readonly=True,
                       stored=True)
    crop_id = fields.Many2one('agri.farm.field.crop',
                              string='Crop',
                              states={'draft': [('readonly', False)]},
                              readonly=True,
                              required=True)
    field_id = fields.Many2one(related='crop_id.field_id', store=True)
    farm_id = fields.Many2one(related='crop_id.farm_id', store=True)
    date = fields.Date('Date',
                       default=fields.Date.context_today,
                       states={'draft': [('readonly', False)]},
                       readonly=True,
                       required=True)
    area = fields.Float('Area',
                        digits='Hectare',
                        states={'draft': [('readonly', False)]},
                        readonly=True)
    area_uom_id = fields.Many2one(related='farm_id.area_uom_id', store=True)
    centroid = fields.GeoPoint('Centroid',
                               srid=4326,
                               gist_index=True,
                               states={'draft': [('readonly', False)]},
                               readonly=True)
    type = fields.Selection(selection=[('disease', 'Disease'),
                                       ('fading', 'Fading'),
                                       ('uneven', 'Uneven'),
                                       ('other', 'Other'), ('root', 'Root'),
                                       ('shortage', 'Shortage'),
                                       ('weed', 'Weed')],
                            string='Type',
                            states={'draft': [('readonly', False)]},
                            readonly=True,
                            required=True)
    description = fields.Char('Description',
                              states={'draft': [('readonly', False)]},
                              readonly=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'agri_farm_field_crop_problem_ir_attachments_rel',
        'problem_id',
        'attachment_id',
        string='Attachments',
        states={'draft': [('readonly', False)]},
        readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('posted', 'Posted')],
                             string='State',
                             default='draft',
                             readonly=True,
                             copy=False,
                             tracking=True)

    @api.depends('type', 'field_id')
    @api.onchange('type', 'field_id')
    def _compute_name(self):
        type_dict = dict(self._fields['type'].selection)
        for problem in self:
            problem.name = _('%s on %s') % (type_dict.get(
                problem.type), problem.field_id.name)

    @api.constrains('description')
    def _constrains_description(self):
        for problem in self:
            if problem.type == 'other' and (not problem.description
                                            or len(problem.description) == 0):
                raise ValidationError(
                    _("Description required for type 'Other'"))

    def action_post(self):
        for problem in self:
            problem.state = 'posted'

    @api.model
    def create(self, vals):
        problem = super(FarmFieldCropProblem, self).create(vals)
        problem.message_subscribe([problem.farm_id.partner_id.id])
        return problem

    def write(self, vals):
        res = super(FarmFieldCropProblem, self).write(vals)
        if 'state' in vals:
            problem = self.browse(self.id)
            body = _(
                "%s <a href=# data-oe-model=%s data-oe-id=%d>%s</a> reported on %s"
            ) % (self._description, self._name, self.id, self.name,
                 format_date(self.env, problem.date)) + (
                     _(":\n\n%s") %
                     (self.description, ) if self.description else '')
            self.crop_id._message_log(body=body)
        return res


class FarmFieldCropZone(models.Model):
    _name = 'agri.farm.field.crop.zone'
    _description = 'Crop Zone'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'crop_id, farm_id desc'

    name = fields.Char('Name',
                       compute='_compute_name',
                       readonly=True,
                       stored=True)
    crop_id = fields.Many2one('agri.farm.field.crop',
                              string='Crop',
                              states={'draft': [('readonly', False)]},
                              readonly=True,
                              required=True)
    product_category_id = fields.Many2one(
        related='crop_id.product_category_id')
    field_id = fields.Many2one(related='crop_id.field_id', store=True)
    farm_id = fields.Many2one(related='crop_id.farm_id', store=True)
    product_id = fields.Many2one(
        'product.product',
        string='Cultivar',
        domain="[('categ_id', '=', product_category_id)]",
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        tracking=True)
    area_uom_id = fields.Many2one(related='farm_id.area_uom_id', store=True)
    planted_area = fields.Float('Planted Area',
                                digits='Hectare',
                                states={
                                    'draft': [('readonly', False)],
                                },
                                readonly=True,
                                required=True,
                                tracking=True)
    planted_date = fields.Date('Planted Date',
                               states={
                                   'draft': [('readonly', False)],
                               },
                               readonly=True,
                               required=True,
                               tracking=True)
    emerged_area = fields.Float('Emerged Area',
                                digits='Hectare',
                                states={
                                    'draft': [('readonly', False)],
                                    'planted': [('readonly', False),
                                                ('required', True)]
                                },
                                readonly=True,
                                tracking=True)
    emerged_date = fields.Date('Emerged Date',
                               states={
                                   'draft': [('readonly', False)],
                                   'planted': [('readonly', False),
                                               ('required', True)]
                               },
                               readonly=True,
                               tracking=True)
    harvested_date = fields.Date('Harvested Date',
                                 states={
                                     'draft': [('readonly', False)],
                                     'emerged': [('readonly', False),
                                                 ('required', True)]
                                 },
                                 readonly=True,
                                 tracking=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'agri_farm_field_crop_zone_ir_attachments_rel',
        'zone_id',
        'attachment_id',
        string='Attachments')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('planted', 'Planted'),
                                        ('emerged', 'Emerged'),
                                        ('harvested', 'Harvested')],
                             string='State',
                             default='draft',
                             readonly=True,
                             copy=False,
                             tracking=True)

    @api.depends('product_id', 'field_id')
    @api.onchange('product_id', 'field_id')
    def _compute_name(self):
        for zone in self:
            zone.name = _('%s on %s') % (zone.product_id.name,
                                         zone.field_id.name)

    def action_plant(self):
        for zone in self:
            zone.state = 'planted'

    def action_emerge(self):
        for zone in self:
            zone.state = 'emerged'

    def action_harvest(self):
        for zone in self:
            zone.state = 'harvested'

    def _message_create(self, values_list):
        if not isinstance(values_list, (list)):
            values_list = [values_list]
        res = super(FarmFieldCropZone, self)._message_create(values_list)
        for values in values_list:
            log_values = {
                key: values[key]
                for key in values.keys()
                & {'tracking_value_ids', 'attachment_ids'}
            }
            body = (
                values.get('body') if 'body' in values
                and len(values.get('body')) else _('%s updated:') %
                (self._description, )).replace(
                    self._description,
                    _("%s <a href=# data-oe-model=%s data-oe-id=%d>%s</a>") %
                    (self._description, self._name, self.id, self.name))
            self.crop_id._message_log(**log_values, body=body)

    @api.model
    def create(self, vals):
        zone_vals = {
            key: vals[key]
            for key in self._fields.keys() if key in vals
        }
        zone = super(FarmFieldCropZone, self).create(zone_vals)
        zone.message_subscribe([zone.farm_id.partner_id.id])
        return zone


class FarmParcel(models.Model):
    _name = 'agri.farm.parcel'
    _description = 'Farm Parcel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'

    farm_id = fields.Many2one('agri.farm',
                              'Farm',
                              ondelete='cascade',
                              required=True)
    name = fields.Char('Name', required=True, tracking=True)
    short_name = fields.Char('Short Name', required=True, tracking=True)
    code = fields.Char('Code', required=True, tracking=True)
    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 tracking=True)
    area = fields.Float('Area', digits='Hectare', tracking=True)
    area_uom_id = fields.Many2one(related='farm_id.area_uom_id', store=True)
    boundary = fields.GeoMultiPolygon('Boundary', srid=4326, gist_index=True)
    has_boundary = fields.Boolean('Has Boundary',
                                  compute='_compute_has_boundary',
                                  default=False)
    farm_version_id = fields.Many2one(related='farm_id.farm_version_id',
                                      readonly=True)
    land_cover_ids = fields.One2many(comodel_name='agri.land.cover',
                                     inverse_name='farm_parcel_id',
                                     string='Land Cover',
                                     copy=True)

    @api.onchange('boundary')
    def _compute_has_boundary(self):
        for land in self:
            land.has_boundary = True if land.boundary else False

    @api.constrains('code')
    def _check_code(self):
        domain = [('farm_id', '=', self.farm_id.id),
                  ('code', 'ilike', self.code)]
        if self.id:
            domain.append(('id', '!=', self.id))
        land = self.env['agri.farm.parcel'].search(domain, limit=1)
        if land:
            raise ValidationError(_('Duplicate Land'))

    def name_get(self):
        return [(land.id, "{} ({:.3f} {})".format(land.name, land.area,
                                                  land.area_uom_id))
                for land in self]

    def _message_create(self, values_list):
        if not isinstance(values_list, (list)):
            values_list = [values_list]
        res = super(FarmParcel, self)._message_create(values_list)
        for values in values_list:
            log_values = {
                key: values[key]
                for key in values.keys()
                & {'tracking_value_ids', 'attachment_ids'}
            }
            body = (
                values.get('body') if 'body' in values
                and len(values.get('body')) else _('%s updated:') %
                (self._description, )).replace(
                    self._description,
                    _("%s <a href=# data-oe-model=%s data-oe-id=%d>%s</a>") %
                    (self._description, self._name, self.id, self.name))
            self.farm_id._message_log(**log_values, body=body)

    @api.model
    def create(self, vals):
        parcel = super(FarmParcel, self).create(vals)
        parcel.message_subscribe([parcel.farm_id.partner_id.id])
        return parcel


class FarmVersion(models.Model):
    _name = 'agri.farm.version'
    _description = 'Farm Version'
    _order = 'date DESC'
    _check_company_auto = True

    name = fields.Char('Name',
                       compute='_compute_name',
                       readonly=True,
                       stored=True)
    date = fields.Date('Date',
                       default=fields.Date.context_today,
                       required=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 ondelete='cascade',
                                 required=True)
    company_id = fields.Many2one('res.company',
                                 required=True,
                                 default=lambda self: self.env.company)
    parent_farm_version_id = fields.Many2one(
        'agri.farm.version',
        'Preceding Version',
        domain="[('partner_id', '=', partner_id)]")
    child_farm_version_ids = fields.Many2many(
        'agri.farm.version',
        'agri_farm_version_rel',
        'farm_version_id',
        'child_id',
        string='Following Versions',
        domain="[('partner_id', '=', partner_id), ('id', '!=', id)]")
    farm_ids = fields.One2many(comodel_name='agri.farm',
                               inverse_name='farm_version_id',
                               string='Farms',
                               copy=True)

    @api.depends('date')
    @api.onchange('date')
    def _compute_name(self):
        for farm_version in self:
            farm_version.name = 'As of {}'.format(
                format_date(self.env, farm_version.date))

    @api.model
    def create(self, vals):
        farm_version = super().create(vals)
        if farm_version.parent_farm_version_id:
            default = {'farm_version_id': farm_version.id}
            farm_commands = []
            for farm in farm_version.parent_farm_version_id.farm_ids:
                farm_copy = farm.copy(default)
                farm_commands += [(4, farm_copy.id, 0)]
            farm_version.write({'farm_ids': farm_commands})
            farm_version.parent_farm_version_id.write(
                {'child_farm_version_ids': [(4, farm_version.id, 0)]})
            latest_farm_version = self.env['agri.farm.version'].search(
                [('partner_id', '=', farm_version.partner_id.id)],
                limit=1,
                order='date DESC')
            farm_version.partner_id.write(
                {'farm_version_id': latest_farm_version.id})
        return farm_version

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, parent_farm_version_id=self)
        return super(FarmVersion, self).copy(default)


class FarmLandUse(models.Model):
    _name = 'agri.farm.land.use'
    _description = 'Farm Land Use'
    _order = 'area desc'

    farm_id = fields.Many2one('agri.farm',
                              'Parcel',
                              ondelete='cascade',
                              required=True)
    land_use_id = fields.Many2one('agri.land.use',
                                  'Land Use',
                                  ondelete='cascade',
                                  required=True)
    area = fields.Float('Area', digits='Hectare', required=True)
    area_uom_id = fields.Many2one(related='farm_id.area_uom_id', store=True)
