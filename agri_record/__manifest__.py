# Copyright 2020 Agrista GmbH (https://agrista.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Agri Record",
    "summary": "Agriculture Activities & Production record keeping",
    "website": "https://github.com/agrista/odoo-agri",
    "category": "Operations/Inventory",
    "version": "0.1.0",
    "sequence": 1,
    "author": "Agrista (Pty) Ltd.",
    "license": "AGPL-3",
    "description": "Agriculture Activities & Production record keeping",
    "depends": ['base', 'stock'],
    "data": [
        'security/ir.model.access.csv',
        'data/res_company_data.xml',
        'views/agri_menus.xml',
        'views/agri_production_record_views.xml',
    ],
    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
