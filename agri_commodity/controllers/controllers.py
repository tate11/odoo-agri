# -*- coding: utf-8 -*-
# from odoo import http


# class AgriCommodity(http.Controller):
#     @http.route('/agri_commodity/agri_commodity/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/agri_commodity/agri_commodity/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('agri_commodity.listing', {
#             'root': '/agri_commodity/agri_commodity',
#             'objects': http.request.env['agri_commodity.agri_commodity'].search([]),
#         })

#     @http.route('/agri_commodity/agri_commodity/objects/<model("agri_commodity.agri_commodity"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('agri_commodity.object', {
#             'object': obj
#         })
