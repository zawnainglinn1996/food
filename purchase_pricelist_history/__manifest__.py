# -*- coding: utf-8 -*-
{
    'name': "Purchase Price-list History",
    'summary': """
        Purchase Product Price-list Record""",
    'description': """
        Record of purchase product based on different price-list
    """,
    'author': "AsiaMatrix",
    'website': "http://www.asiamatrixsoftware.com",
    'category': 'Purchase',
    'version': '1.4',
    'license': 'OPL-1',
    'depends': [
        'purchase',
        'multi_uom'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pricelist_record_view.xml',
        'views/purchase_order_view.xml',
    ],
    'images': ['static/description/icon.png'],
}