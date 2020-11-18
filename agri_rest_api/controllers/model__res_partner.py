# -*- coding: utf-8 -*-
from odoo.addons.rest_api.controllers.main import *
from odoo.addons.rest_api.controllers import model__res_partner as ResPartnerController


class AgriControllerREST(ResPartnerController.ControllerREST):
    def __init__(self):
        super(AgriControllerREST, self).__init__()
        self.OUT__res_partner__read_all__SCHEMA.extend([
            # many2one fields:
            ('farm_version_id', ('id', 'name')),
        ])
        self.OUT__res_partner__read_one__SCHEMA.extend([
            # many2one fields:
            ('farm_version_id', ('id', 'name')),
            # one2many field:
            (
                'farm_ids',
                [(
                    'id',
                    'area',
                    'boundary',
                    'name',
                    # many2one fields:
                    ('area_uom_id', ('id', 'name')),
                    # one2many field:
                    (
                        'farm_field_ids',
                        [(
                            'id',
                            'area',
                            'boundary',
                            'farm_id',
                            'name',
                            # many2one fields:
                            ('area_uom_id', ('id', 'name')))]),
                    (
                        'farm_parcel_ids',
                        [(
                            'id',
                            'area',
                            'boundary',
                            'code',
                            'farm_id',
                            'short_name'
                            'name',
                            # many2one fields:
                            ('area_uom_id', ('id', 'name')),
                            ('country_id', (
                                'id',
                                'name',
                                'code',
                            )))]))]),
        ])
        self.OUT__res_partner__create_one__SCHEMA.extend([
            # many2one fields:
            ('farm_version_id', ('id', 'name')),
        ])
