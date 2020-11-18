# -*- coding: utf-8 -*-
from odoo.addons.rest_api.controllers.main import *
from odoo.addons.rest_api.controllers import model__res_users as ResUsersController


class AgriControllerREST(ResUsersController.ControllerREST):
    def __init__(self):
        super(AgriControllerREST, self).__init__()
        partner_ids = [
            item for item in self.OUT__res_users__create_one__SCHEMA
            if isinstance(item, tuple) and item[0] == 'partner_id'
        ]
        self.OUT__res_users__create_one__SCHEMA = [
            item for item in self.OUT__res_users__create_one__SCHEMA
            if not isinstance(item, tuple) or item[0] != 'partner_id'
        ]
        for partner_id in partner_ids:
            vals = list(partner_id[1])
            vals.append(('farm_version_id', ('id', 'name')))
            self.OUT__res_users__create_one__SCHEMA.extend([('partner_id',
                                                             tuple(vals))])
