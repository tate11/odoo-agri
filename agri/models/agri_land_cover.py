from odoo import api, fields, models


class AgriLandCover(models.Model):
    _name = 'agri.landcover'
    _description = 'Land Cover'
    _order = 'area_ha desc'

    land_class_id = fields.Many2one('agri.landclass',
                                    'Land Class',
                                    ondelete='cascade',
                                    required=True)
    area_ha = fields.Float('Hectares', required=True)
    land_id = fields.Many2one('agri.land',
                              'Land',
                              ondelete='cascade',
                              required=True)
