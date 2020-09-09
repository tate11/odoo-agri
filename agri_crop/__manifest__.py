# Copyright 2020 Agrista GmbH (https://agrista.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Agri Crop",
    "summary": "Agriculture module to add Crops",
    "website": "https://github.com/agrista/odoo-agri",
    "category": "Operations/Inventory",
    "version": "0.1.0",
    "sequence": 1,
    "author": "Agrista (Pty) Ltd.",
    "license": "AGPL-3",
    "description": "Agriculture module to add Crops",
    "depends": ['base', 'product', 'agri'],
    "data": [
        'security/ir.model.access.csv',
        'views/agri_crop_menus.xml',
        'views/product_views.xml',
    ],
    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
