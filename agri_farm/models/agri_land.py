from odoo import api, fields, models


class LandCover(models.Model):
    _name = 'agri.land.cover'
    _description = 'Land Cover'
    _order = 'area_ha desc'

    land_use_id = fields.Many2one('agri.land.use',
                                  'Land Use',
                                  ondelete='cascade',
                                  required=True)
    area_ha = fields.Float('Hectares', digits='Hectare', required=True)
    farm_parcel_id = fields.Many2one('agri.farm.parcel',
                                     'Parcel',
                                     ondelete='cascade',
                                     required=True)
