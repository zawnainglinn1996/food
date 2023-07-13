# -*- coding: utf-8 -*-
{
    'name': "Purchase Extend",

    'summary': """Purchase Extend""",

    'description': """
        1.For Purchase Extend
    """,

    'author': "asiamatrix",
    'website': "http://www.blue-stone.net",

    'category': 'purchase',
    'version': '3.0',
    'license': "LGPL-3",
    'depends': [
        'account',
        'purchase',
        'submission_of_quotation',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/purchase_log_note_template_inherit.xml',
        'security/purchase_security_access_group.xml',
        'views/purchase_order_view.xml',
        'views/account_move_view.xml',

    ],

}
