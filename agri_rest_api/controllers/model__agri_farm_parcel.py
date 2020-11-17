# -*- coding: utf-8 -*-
from odoo.addons.rest_api.controllers.main import *

_logger = logging.getLogger(__name__)

# List of REST resources in current file:
#   (url prefix)                (method)     (action)
# /api/agri.farm.parcel                GET     - Read all (with optional filters, offset, limit, order)
# /api/agri.farm.parcel/<id>           GET     - Read one
# /api/agri.farm.parcel                POST    - Create one
# /api/agri.farm.parcel/<id>           PUT     - Update one
# /api/agri.farm.parcel/<id>           DELETE  - Delete one
# /api/agri.farm.parcel/<id>/<method>  PUT     - Call method (with optional parameters)

# List of IN/OUT data (json data and HTTP-headers) for each REST resource:

# /api/agri.farm.parcel  GET  - Read all (with optional filters, offset, limit, order)
# IN data:
#   HEADERS:
#       'access_token'
#   JSON:
#       (optional filters (Odoo domain), offset, limit, order)
#           {                                       # editable
#               "filters": [('some_field_1', '=', some_value_1), ('some_field_2', '!=', some_value_2), ...],
#               "offset":  XXX,
#               "limit":   XXX,
#               "order":   "list_of_fields"  # default 'name asc'
#           }
# OUT data:
OUT__agri_farm_parcel__read_all__SUCCESS_CODE = 200  # editable
#   JSON:
#       {
#           "count":   XXX,     # number of returned records
#           "results": [
OUT__agri_farm_parcel__read_all__SCHEMA = (  # editable
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
    )),
)
#           ]
#       }

# /api/agri.farm.parcel/<id>  GET  - Read one
# IN data:
#   HEADERS:
#       'access_token'
#   JSON:
#       (optional parameter 'search_field' for search object not by 'id' field)
#           {"search_field": "some_field_name"}     # editable
# OUT data:
OUT__agri_farm_parcel__read_one__SUCCESS_CODE = 200  # editable
OUT__agri_farm_parcel__read_one__SCHEMA = (  # editable
    # (The order of fields of different types maybe arbitrary)
    # simple fields (non relational):
    'id',
    'area',
    'boundary',
    'code',
    'short_name',
    'name',
    # many2one fields:
    ('area_uom_id', ('id', 'name')),
    ('country_id', (
        'id',
        'name',
        'code',
    )),
    ('farm_id', ('id', 'name')),
)

# /api/agri.farm.parcel  POST  - Create one
# IN data:
#   HEADERS:
#       'access_token'
#   DEFAULTS:
#       (optional default values of fields)
DEFAULTS__agri_farm_parcel__create_one__JSON = {  # editable
    # "some_field_1": some_value_1,
    # "some_field_2": some_value_2,
    # ...
}
#   JSON:
#       (fields and its values of created object;
#        don't forget about model's mandatory fields!)
#           ...                                     # editable
# OUT data:
OUT__agri_farm_parcel__create_one__SUCCESS_CODE = 200  # editable
OUT__agri_farm_parcel__create_one__SCHEMA = (  # editable
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
    )),
)

# /api/agri.farm.parcel/<id>  PUT  - Update one
# IN data:
#   HEADERS:
#       'access_token'
#   JSON:
#       (fields and new values of updated object)   # editable
#           ...
# OUT data:
OUT__agri_farm_parcel__update_one__SUCCESS_CODE = 200  # editable

# /api/agri.farm.parcel/<id>  DELETE  - Delete one
# IN data:
#   HEADERS:
#       'access_token'
# OUT data:
OUT__agri_farm_parcel__delete_one__SUCCESS_CODE = 200  # editable

# /api/agri.farm.parcel/<id>/<method>  PUT  - Call method (with optional parameters)
# IN data:
#   HEADERS:
#       'access_token'
#   JSON:
#       (named parameters of method)                # editable
#           ...
# OUT data:
OUT__agri_farm_parcel__call_method__SUCCESS_CODE = 200  # editable

# HTTP controller of REST resources:


class ControllerREST(http.Controller):

    # Read all (with optional filters, offset, limit, order):
    @http.route('/api/agri.farm.parcel',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_parcel__GET(self, **kw):
        return wrap__resource__read_all(
            modelname='agri.farm.parcel',
            default_domain=[],
            success_code=OUT__agri_farm_parcel__read_all__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm_parcel__read_all__SCHEMA)

    # Read one:
    @http.route('/api/agri.farm.parcel/<id>',
                methods=['GET', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True)
    @check_permissions
    def api__agri_farm_parcel__id_GET(self, id, **kw):
        return wrap__resource__read_one(
            modelname='agri.farm.parcel',
            id=id,
            success_code=OUT__agri_farm_parcel__read_one__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm_parcel__read_one__SCHEMA)

    # Create one:
    @http.route('/api/agri.farm.parcel',
                methods=['POST', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_parcel__POST(self, **kw):
        return wrap__resource__create_one(
            modelname='agri.farm.parcel',
            default_vals=DEFAULTS__agri_farm_parcel__create_one__JSON,
            success_code=OUT__agri_farm_parcel__create_one__SUCCESS_CODE,
            OUT_fields=OUT__agri_farm_parcel__create_one__SCHEMA)

    # Update one:
    @http.route('/api/agri.farm.parcel/<id>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_parcel__id_PUT(self, id, **kw):
        return wrap__resource__update_one(
            modelname='agri.farm.parcel',
            id=id,
            success_code=OUT__agri_farm_parcel__update_one__SUCCESS_CODE)

    # Delete one:
    @http.route('/api/agri.farm.parcel/<id>',
                methods=['DELETE', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_parcel__id_DELETE(self, id, **kw):
        return wrap__resource__delete_one(
            modelname='agri.farm.parcel',
            id=id,
            success_code=OUT__agri_farm_parcel__delete_one__SUCCESS_CODE)

    # Call method (with optional parameters):
    @http.route('/api/agri.farm.parcel/<id>/<method>',
                methods=['PUT', 'OPTIONS'],
                type='http',
                auth='none',
                cors=True,
                csrf=False)
    @check_permissions
    def api__agri_farm_parcel__id__method_PUT(self, id, method, **kw):
        return wrap__resource__call_method(
            modelname='agri.farm.parcel',
            id=id,
            method=method,
            success_code=OUT__agri_farm_parcel__call_method__SUCCESS_CODE)
