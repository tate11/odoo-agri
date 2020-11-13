from odoo import api, fields, models


class LandCover(models.Model):
    _name = 'agri.land.cover'
    _description = 'Land Cover'
    _order = 'area desc'

    farm_parcel_id = fields.Many2one('agri.farm.parcel',
                                     'Parcel',
                                     ondelete='cascade',
                                     required=True)
    land_use_id = fields.Many2one('agri.land.use',
                                  'Land Use',
                                  ondelete='cascade',
                                  required=True)
    area = fields.Float('Area', digits='Hectare', required=True)
    area_uom_id = fields.Many2one(related='farm_parcel_id.area_uom_id',
                                  store=True)
