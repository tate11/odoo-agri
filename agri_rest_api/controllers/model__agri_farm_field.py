from odoo.addons.rest_api.controllers.main import *

_logger = logging.getLogger(__name__)

OUT__agri_farm_field__read_all__SUCCESS_CODE = 200
OUT__agri_farm_field__read_all__SCHEMA = (
    'id',
    'area',
    'boundary',
    'name',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
    ('farm_id', ('id', 'name')),
)

OUT__agri_farm_field__read_one__SUCCESS_CODE = 200
OUT__agri_farm_field__read_one__SCHEMA = (
    'id',
    'area',
    'boundary',
    'name',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
    ('farm_id', ('id', 'name')),
    # one2many field:
    (
        'crop_ids',
        [(
            'id',
            'cleared_date',
            'emerged_area',
            'established_date',
            'field_id',
            'name',
            'planted_area',
            'state',
            # many2one fields:
            ('product_category_id', ('id', 'name')),
            # one2many field:
            (
                'problem_ids',
                [(
                    'id',
                    'area',
                    'centroid',
                    'crop_id',
                    'date',
                    'description',
                    'type',
                    'state',
                    # many2one fields:
                    ('area_uom_id', ('id', 'name')),
                )]),
            (
                'zone_ids',
                [(
                    'id',
                    'emerged_area',
                    'emerged_date',
                    'harvested_date',
                    'planted_area',
                    'planted_date',
                    'crop_id',
                    'state',
                    # many2one fields:
                    ('area_uom_id', ('id', 'name')),
                    ('product_id', ('id', 'name')),
                )]),
        )]),
)

DEFAULTS__agri_farm_field__create_one__JSON = {}
OUT__agri_farm_field__create_one__SUCCESS_CODE = 200
OUT__agri_farm_field__create_one__SCHEMA = (
    'id',
    'area',
    'area_uom_id',
    'boundary',
    'farm_id',
    'name',
)

OUT__agri_farm_field__update_one__SUCCESS_CODE = 200

OUT__agri_farm_field__delete_one__SUCCESS_CODE = 200

OUT__agri_farm_field__call_method__SUCCESS_CODE = 200


class ControllerREST(http.Controller):

    # Read all (with optional filters, offset, limit, order):
    @http.route('/api/agri.farm.field',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_field__GET(self, **kw):
        return wrap__resource__read_all(
            modelname='agri.farm.field',
            default_domain=[],
            success_code=OUT__agri_farm_field__read_all__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm_field__read_all__SCHEMA)

    # Read one:
    @http.route('/api/agri.farm.field/<id>',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_field__id_GET(self, id, **kw):
        return wrap__resource__read_one(
            modelname='agri.farm.field',
            id=id,
            success_code=OUT__agri_farm_field__read_one__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm_field__read_one__SCHEMA)

    # Create one:
    @http.route('/api/agri.farm.field',
                methods=['POST', 'OPTIONS'],
                type='http',
                auth='admin',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field__POST(self, **kw):
        return wrap__resource__create_one(
            modelname='agri.farm.field',
            default_vals=DEFAULTS__agri_farm_field__create_one__JSON,
            success_code=OUT__agri_farm_field__create_one__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm_field__create_one__SCHEMA)

    # Update one:
    @http.route('/api/agri.farm.field/<id>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field__id_PUT(self, id, **kw):
        return wrap__resource__update_one(
            modelname='agri.farm.field',
            id=id,
            success_code=OUT__agri_farm_field__update_one__SUCCESS_CODE)

    # Delete one:
    @http.route('/api/agri.farm.field/<id>',
                methods=['DELETE', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field__id_DELETE(self, id, **kw):
        return wrap__resource__delete_one(
            modelname='agri.farm.field',
            id=id,
            success_code=OUT__agri_farm_field__delete_one__SUCCESS_CODE)

    # Call method (with optional parameters):
    @http.route('/api/agri.farm.field/<id>/<method>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field__id__method_PUT(self, id, method, **kw):
        return wrap__resource__call_method(
            modelname='agri.farm.field',
            id=id,
            method=method,
            success_code=OUT__agri_farm_field__call_method__SUCCESS_CODE)
