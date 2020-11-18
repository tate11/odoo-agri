from odoo.addons.rest_api.controllers.main import *

_logger = logging.getLogger(__name__)

OUT__agri_farm__read_all__SUCCESS_CODE = 200
OUT__agri_farm__read_all__SCHEMA = (
    'id',
    'area',
    'boundary',
    'name',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
)

OUT__agri_farm__read_one__SUCCESS_CODE = 200
OUT__agri_farm__read_one__SCHEMA = (
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
            'short_name',
            'name',
            # many2one fields:
            ('area_uom_id', ('id', 'name')),
            ('country_id', (
                'id',
                'name',
                'code',
            )))]))

DEFAULTS__agri_farm__create_one__JSON = {}
OUT__agri_farm__create_one__SUCCESS_CODE = 200
OUT__agri_farm__create_one__SCHEMA = (
    'id',
    'area',
    'boundary',
    'name',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
)

OUT__agri_farm__update_one__SUCCESS_CODE = 200

OUT__agri_farm__delete_one__SUCCESS_CODE = 200

OUT__agri_farm__call_method__SUCCESS_CODE = 200


class ControllerREST(http.Controller):

    # Read all (with optional filters, offset, limit, order):
    @http.route('/api/agri.farm',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm__GET(self, **kw):
        return wrap__resource__read_all(
            modelname='agri.farm',
            default_domain=[],
            success_code=OUT__agri_farm__read_all__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm__read_all__SCHEMA)

    # Read one:
    @http.route('/api/agri.farm/<id>',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm__id_GET(self, id, **kw):
        return wrap__resource__read_one(
            modelname='agri.farm',
            id=id,
            success_code=OUT__agri_farm__read_one__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm__read_one__SCHEMA)

    # Create one:
    @http.route('/api/agri.farm',
                methods=['POST', 'OPTIONS'],
                type='http',
                auth='admin',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm__POST(self, **kw):
        return wrap__resource__create_one(
            modelname='agri.farm',
            default_vals=DEFAULTS__agri_farm__create_one__JSON,
            success_code=OUT__agri_farm__create_one__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm__create_one__SCHEMA)

    # Update one:
    @http.route('/api/agri.farm/<id>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm__id_PUT(self, id, **kw):
        return wrap__resource__update_one(
            modelname='agri.farm',
            id=id,
            success_code=OUT__agri_farm__update_one__SUCCESS_CODE)

    # Delete one:
    @http.route('/api/agri.farm/<id>',
                methods=['DELETE', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm__id_DELETE(self, id, **kw):
        return wrap__resource__delete_one(
            modelname='agri.farm',
            id=id,
            success_code=OUT__agri_farm__delete_one__SUCCESS_CODE)

    # Call method (with optional parameters):
    @http.route('/api/agri.farm/<id>/<method>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm__id__method_PUT(self, id, method, **kw):
        return wrap__resource__call_method(
            modelname='agri.farm',
            id=id,
            method=method,
            success_code=OUT__agri_farm__call_method__SUCCESS_CODE)
