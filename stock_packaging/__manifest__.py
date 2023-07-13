# -*- coding: utf-8 -*-
{
    'name': 'Stock Packaging',
    'version': '1.6',
    'category': 'Stock',
    'sequence': 100,
    'summary': 'To package products.',
    'author': 'Asia Matrix',
    'depends': [
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/stock_location.xml',
        'data/assign_package_location_id.xml',
        'views/stock_packaging_views.xml',
        'views/product_views.xml',
        'views/res_config_settings_views.xml',
        'wizards/show_insufficient_qty_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
