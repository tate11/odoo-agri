# Copyright 2020 Agrista GmbH (https://agrista.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base Agri",
    "summary": "Base Agriculture module to add Farms & Fields",
    "website": "https://github.com/agrista/odoo-agri",
    "category": "Operations/Inventory",
    "version": "0.1.0",
    "sequence": 1,
    "author": "Agrista (Pty) Ltd.",
    "license": "AGPL-3",
    "description": "Base Agriculture module to add Farms & Fields",
    "depends": ['base', 'base_geoengine'],
    "data": [
        'data/cropping_potential_data.xml',
        'data/effective_depth_data.xml',
        'data/irrigation_type_data.xml',
        'data/land_class_data.xml',
        'data/soil_texture_data.xml',
        'data/terrain_data.xml',
        'data/water_source_data.xml',
        'data/water_source_data.xml',
        'data/res_partner_data.xml',
    ],
    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
