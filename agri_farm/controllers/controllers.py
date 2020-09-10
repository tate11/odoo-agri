# -*- coding: utf-8 -*-
# from odoo import http


# class AgriFarm(http.Controller):
#     @http.route('/agri_farm/agri_farm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/agri_farm/agri_farm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('agri_farm.listing', {
#             'root': '/agri_farm/agri_farm',
#             'objects': http.request.env['agri_farm.agri_farm'].search([]),
#         })

#     @http.route('/agri_farm/agri_farm/objects/<model("agri_farm.agri_farm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('agri_farm.object', {
#             'object': obj
#         })
