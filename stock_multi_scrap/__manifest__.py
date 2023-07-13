# -*- coding: utf-8 -*-
{
    'name': 'Multi Scrap',

    'version': '1.8',

    'license': 'LGPL-3',

    'summary': 'Multi Scrap Form',

    'description': """
       * Added menu multi scrap in inventory module. 
    """,

    'category': 'Stock',

    'website': "www.asiamatrixsoftware.com",

    'email': 'info@asiamatrixsoftware.com',

    'depends': [
        'stock',
        'mrp',
        'multi_employee_login'

    ],

    'data': [
        'data/stock_multi_scrap.xml',
        'security/ir.model.access.csv',
        'views/scrap_views.xml',
        'wizard/stock_warn_insufficient_qty_views.xml',
        'report/multi_scrap_report_views.xml',
    ],

    'installable': True,

    'application': False,

    'auto_install': False,
}
