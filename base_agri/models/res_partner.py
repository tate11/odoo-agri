from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    farmland_id = fields.Many2one('agri.farmland', 'Farmland')
    farmland_ids = fields.One2many(
        comodel_name='agri.farmland',
        inverse_name='partner_id',
        string='Farmlands',
    )
