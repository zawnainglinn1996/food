# -*- coding: utf-8 -*-
{
    'name': 'Stock Backdate',

    'version': '1.8',

    'summary': 'All Module Backdate',

    'description': """
       * Stock Inventory Adjusment Backdate.
       * Stock Move and Move line Backdate.
       * Stock Valuation Layer Backdate.
       * Stock Picking Backdate.
       * Stock Scrap Backdate.
       * Sale Order Backdate.
       * Purchase Order Backdate.
       * Invoicing Backdate.
    """,

    'category': 'Stock',

    'Author': 'Asia Matrix Co.,Ltd',

    'website': "www.asiamatrixsoftware.com",

    'email': 'info@asiamatrixsoftware.com',

    'license': "LGPL-3",

    'depends': [
        'stock_account',
        'sale_stock',
        'purchase',
        'account',
        'stock_multi_scrap',
    ],

    'data': [
        'views/stock_scrap_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_valuation_layer_views.xml',
    ],

    'installable': True,

    'application': False,

    'auto_install': False,
}
