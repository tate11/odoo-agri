from odoo import api, fields, models


class AgriLandCover(models.Model):
    _name = 'agri.landcover'
    _description = 'Land Cover'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    area_ha = fields.Boolean('Hectares', required=True)
    land_id = fields.Many2one('agri.land',
                              'Land',
                              ondelete='cascade',
                              required=True)
