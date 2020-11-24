# -*- coding: utf-8 -*-
{
    'name': "Agri Commodities",
    'summary': """
        Agricultural commodities and grading""",
    'description': """
        Manage the grading of agricultural commodities
    """,
    'author': "Agrista GmbH",
    'website': "https://agrista.com",
    'category': 'Manufacturing',
    'version': '0.1',
    'depends': ['agri', 'product', 'stock'],
    'data': [
        'data/agri_delivery_sequence.xml',
        'security/ir.model.access.csv',
        'views/agri_delivery_views.xml',
        'views/agri_grading_views.xml',
        'views/product_views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
