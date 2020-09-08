from odoo import api, fields, models


class AgriCroppingPotential(models.Model):
    _name = 'agri.croppingpotential'
    _description = 'Cropping Potential'

    name = fields.Char('Name', required=True)
