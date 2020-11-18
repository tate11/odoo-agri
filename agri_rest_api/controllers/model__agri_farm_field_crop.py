from odoo.addons.rest_api.controllers.main import *

_logger = logging.getLogger(__name__)

OUT__read_all__SUCCESS_CODE = 200
OUT__read_all__SCHEMA = (
    'id',
    'cleared_date',
    'emerged_area',
    'established_date',
    'name',
    'planted_area',
    'state',
    # many2one fields:
    ('field_id', ('id', 'name')),
    ('product_category_id', ('id', 'name')),
)

OUT__read_one__SUCCESS_CODE = 200
OUT__read_one__SCHEMA = (
    'id',
    'cleared_date',
    'emerged_area',
    'established_date',
    'name',
    'planted_area',
    'state',
    # many2one fields:
    ('field_id', ('id', 'name')),
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
)

DEFAULTS__create_one__JSON = {}
OUT__create_one__SUCCESS_CODE = 200
OUT__create_one__SCHEMA = (
    'id',
    'cleared_date',
    'emerged_area',
    'established_date',
    'field_id',
    'name',
    'planted_area',
    'product_category_id',
    'state',
)

OUT__update_one__SUCCESS_CODE = 200

OUT__delete_one__SUCCESS_CODE = 200

OUT__call_method__SUCCESS_CODE = 200


class ControllerREST(http.Controller):

    # Read all (with optional filters, offset, limit, order):
    @http.route('/api/agri.farm.field.crop',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_field_crop__GET(self, **kw):
        return wrap__resource__read_all(
            modelname='agri.farm.field.crop',
            default_domain=[],
            success_code=OUT__read_all__SUCCESS_CODE,
            OUT_fields=OUT__read_all__SCHEMA)

    # Read one:
    @http.route('/api/agri.farm.field.crop/<id>',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_field_crop__id_GET(self, id, **kw):
        return wrap__resource__read_one(
            modelname='agri.farm.field.crop',
            id=id,
            success_code=OUT__read_one__SUCCESS_CODE,
            OUT_fields=OUT__read_one__SCHEMA)

    # Create one:
    @http.route('/api/agri.farm.field.crop',
                methods=['POST', 'OPTIONS'],
                type='http',
                auth='admin',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop__POST(self, **kw):
        return wrap__resource__create_one(
            modelname='agri.farm.field.crop',
            default_vals=DEFAULTS__create_one__JSON,
            success_code=OUT__create_one__SUCCESS_CODE,
            OUT_fields=OUT__create_one__SCHEMA)

    # Update one:
    @http.route('/api/agri.farm.field.crop/<id>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop__id_PUT(self, id, **kw):
        return wrap__resource__update_one(
            modelname='agri.farm.field.crop',
            id=id,
            success_code=OUT__update_one__SUCCESS_CODE)

    # Delete one:
    @http.route('/api/agri.farm.field.crop/<id>',
                methods=['DELETE', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop__id_DELETE(self, id, **kw):
        return wrap__resource__delete_one(
            modelname='agri.farm.field.crop',
            id=id,
            success_code=OUT__delete_one__SUCCESS_CODE)

    # Call method (with optional parameters):
    @http.route('/api/agri.farm.field.crop/<id>/<method>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop__id__method_PUT(self, id, method, **kw):
        return wrap__resource__call_method(
            modelname='agri.farm.field.crop',
            id=id,
            method=method,
            success_code=OUT__call_method__SUCCESS_CODE)
