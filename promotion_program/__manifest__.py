# -*- coding: utf-8 -*-
{
    'name': "Promotion Program",
    'summary': "Promotion programs for all sale channels.",
    'description': '',
    'author': "Asia Matrix Software Solution",
    'website': "http://www.asiamatrixsoftware.com",
    'category': 'Sales',
    'version': '2.2',
    'license': "LGPL-3",
    'depends': [
        'point_of_sale',
        'stock',
        'sale_stock', 
        'stock_account',
        'sales_team',
        'account',
        'crm',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/promotion_program_views.xml',
        'views/sale_views.xml',
        'views/pos_views.xml',
        'views/crm_team_views.xml',
        'wizards/get_sale_promotion_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'promotion_program/static/src/css/*',
            'promotion_program/static/src/js/*',
        ],
        'web.assets_qweb': [
            'promotion_program/static/src/xml/*',
        ],
    },
    'installable': True,
    'application': False,
}
