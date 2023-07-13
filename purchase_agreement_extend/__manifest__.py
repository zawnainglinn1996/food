# -*- coding: utf-8 -*-
{
    'name': "Purchase Agreement",

    'summary': """Purchase Agreement""",

    'description': """
        1.For Purchase agreement
    """,

    'author': "asiamatrix",
    'website': "http://www.blue-stone.net",
    'category': 'stock',
    'version': '1.7',
    'license': "LGPL-3",
    'depends': [
        'purchase_requisition',
        'multi_uom',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/purchase_agreement_view.xml',

    ],

}
