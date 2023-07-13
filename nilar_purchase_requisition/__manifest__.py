# -*- coding: utf-8 -*-
{
    'name': "Purchase Requistion Department",

    'summary': """Purchase Requisition""",

    'description': """
        1.For Purchase Stock Requisition by Department
    """,

    'author': "asiamatrix",
    'website': "http://www.blue-stone.net",
    'category': 'stock',
    'version': '3.6',
    'license': "LGPL-3",
    'depends': [
        'product_extend',
        'sale',
        'purchase',
        'account',
        'stock_requestion',
        'stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/purchase_requisition_view.xml',
        'views/account_move_view.xml',
        'views/stock_warehouse_view.xml',
        'security/purchaser_requisition_security.xml',
    ],

}
