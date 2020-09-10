# Copyright 2020 Agrista GmbH (https://agrista.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Agri Farm",
    "summary": "Agriculture module for Farm management",
    "website": "https://github.com/agrista/odoo-agri",
    "category": "Operations/Inventory",
    "version": "0.1.0",
    "sequence": 1,
    "author": "Agrista (Pty) Ltd.",
    "license": "AGPL-3",
    "description": "Agriculture module to add Farm management",
    "depends": ['base', 'base_geoengine', 'mail', 'agri'],
    "data": [
        'security/ir.model.access.csv',
        'data/res_partner_data.xml',
        'views/agri_farm_views.xml',
        'views/res_partner_views.xml',
    ],
    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
