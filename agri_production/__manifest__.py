# Copyright 2020 Agrista GmbH (https://agrista.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name":
    "Agri Production",
    "summary":
    "Agriculture module for Production management",
    "website":
    "https://github.com/agrista/odoo-agri",
    "category":
    "Operations/Inventory",
    "version":
    "0.1.0",
    "sequence":
    1,
    "author":
    "Agrista GmbH",
    "license":
    "AGPL-3",
    "description":
    "Agriculture module for Production management",
    "depends": ['base', 'date_range', 'agri_farm', 'agri_commodity'],
    "data": [
        'security/agri_production_security.xml',
        'security/ir.model.access.csv',
        'data/res_company_data.xml',
        'views/agri_delivery_views.xml',
        'views/agri_production_plan_views.xml',
        'views/agri_production_portal_templates.xml',
        'views/agri_production_record_views.xml',
        'views/date_range_views.xml',
        'views/product_views.xml',
        'views/menus.xml',
        'report/agri_production_report_templates.xml',
        'report/agri_production_report.xml',
    ],
    "demo": [],
    "application":
    True,
    "installable":
    True,
    "auto_install":
    False,
        "uninstall_hook": "uninstall_hook",
}
