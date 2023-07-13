# -*- coding: utf-8 -*-
{
    'name': 'Stock Backdate Report',
    'version': '1.0',
    'summary': 'Stock On Hand Report with Backdate and Location',
    'sequence': 101,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'reports/stock_backdate_report_views.xml',
        'wizards/stock_backdate_report_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'stock_backdate_report/static/src/js/stock_at_date.js',
        ],
        'web.assets_qweb': [
            'stock_backdate_report/static/src/xml/stock_at_date.xml',
        ],
    },
}
