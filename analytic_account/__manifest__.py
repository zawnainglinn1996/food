# -*- coding: utf-8 -*-
{
    'name': 'Analytic Account',
    'version': '2.9',
    'category': 'Accounting',
    'sequence': 1001,
    'summary': 'Analytic account in all journals',
    'author': 'Asia Matrix',
    'depends': [
        'multi_employee_login',
        'stock_account',
        'point_of_sale',
        'stock_landed_costs',
        'purchase',
        'sale',
        'account_asset',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_views.xml',
        'views/account_views.xml',
        'views/account_bank_statement_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_inventory_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_landed_costs_views.xml',
        'views/purchase_views.xml',
        'views/account_payment_views.xml',
        'views/stock_valuation_layer_view.xml',
        'views/account_asset_views.xml',
        'views/shop_to_take_views.xml',
        'views/account_analytic_account_views.xml',
        'views/sale_views.xml',
        'wizards/analytic_account_view.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
