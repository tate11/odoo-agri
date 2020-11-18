from odoo.addons.rest_api.controllers.main import *

_logger = logging.getLogger(__name__)

OUT____read_all__SUCCESS_CODE = 200
OUT____read_all__SCHEMA = (
    'id',
    'emerged_area',
    'emerged_date',
    'harvested_date',
    'planted_area',
    'planted_date',
    'state',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
    ('crop_id', ('id', 'name')),
    ('product_id', ('id', 'name')),
)

OUT____read_one__SUCCESS_CODE = 200
OUT____read_one__SCHEMA = (
    'id',
    'emerged_area',
    'emerged_date',
    'harvested_date',
    'planted_area',
    'planted_date',
    'state',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
    ('crop_id', ('id', 'name')),
    ('product_id', ('id', 'name')),
)

DEFAULTS__create_one__JSON = {}
OUT____create_one__SUCCESS_CODE = 200
OUT____create_one__SCHEMA = (
    'id',
    'area_uom_id',
    'crop_id',
    'emerged_area',
    'emerged_date',
    'harvested_date',
    'planted_area',
    'planted_date',
    'product_id',
    'state',
)

OUT____update_one__SUCCESS_CODE = 200

OUT____delete_one__SUCCESS_CODE = 200

OUT____call_method__SUCCESS_CODE = 200


class ControllerREST(http.Controller):

    # Read all (with optional filters, offset, limit, order):
    @http.route('/api/agri.farm.field.crop.zone',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_field_crop_zone__GET(self, **kw):
        return wrap__resource__read_all(
            modelname='agri.farm.field.crop.zone',
            default_domain=[],
            success_code=OUT____read_all__SUCCESS_CODE,
            OUT_fields=OUT____read_all__SCHEMA)

    # Read one:
    @http.route('/api/agri.farm.field.crop.zone/<id>',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_field_crop_zone__id_GET(self, id, **kw):
        return wrap__resource__read_one(
            modelname='agri.farm.field.crop.zone',
            id=id,
            success_code=OUT____read_one__SUCCESS_CODE,
            OUT_fields=OUT____read_one__SCHEMA)

    # Create one:
    @http.route('/api/agri.farm.field.crop.zone',
                methods=['POST', 'OPTIONS'],
                type='http',
                auth='admin',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop_zone__POST(self, **kw):
        return wrap__resource__create_one(
            modelname='agri.farm.field.crop.zone',
            default_vals=DEFAULTS__create_one__JSON,
            success_code=OUT____create_one__SUCCESS_CODE,
            OUT_fields=OUT____create_one__SCHEMA)

    # Update one:
    @http.route('/api/agri.farm.field.crop.zone/<id>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop_zone__id_PUT(self, id, **kw):
        return wrap__resource__update_one(
            modelname='agri.farm.field.crop.zone',
            id=id,
            success_code=OUT____update_one__SUCCESS_CODE)

    # Delete one:
    @http.route('/api/agri.farm.field.crop.zone/<id>',
                methods=['DELETE', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop_zone__id_DELETE(self, id, **kw):
        return wrap__resource__delete_one(
            modelname='agri.farm.field.crop.zone',
            id=id,
            success_code=OUT____delete_one__SUCCESS_CODE)

    # Call method (with optional parameters):
    @http.route('/api/agri.farm.field.crop.zone/<id>/<method>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_field_crop_zone__id__method_PUT(self, id, method, **kw):
        return wrap__resource__call_method(
            modelname='agri.farm.field.crop.zone',
            id=id,
            method=method,
            success_code=OUT____call_method__SUCCESS_CODE)
