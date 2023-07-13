# -*- coding: utf-8 -*-
{
    'name': 'Account Extend',
    'version': '2.3',
    'category': 'Accounting',
    'sequence': 1001,
    'summary': 'Account Extend',
    'author': 'Asia Matrix',
    'depends': [
        'account',
        'account_asset',
        'stock_landed_costs'
    ],
    'data': [
        'views/accounting_menu_view.xml',
        'views/account_move_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
