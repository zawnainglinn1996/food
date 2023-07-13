# -*- coding: utf-8 -*-
{
    'name': "Purchase Submission Of Q",

    'summary': """Purchase Submission Of Q""",

    'description': """
        1.For Purchase Submission of Quotation
    """,

    'author': "asiamatrix",
    'website': "http://www.blue-stone.net",
    'category': 'stock',
    'version': '3.4',
    'license': "LGPL-3",
    'depends': [
        'nilar_purchase_requisition',
        'sequence_reset_period',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/submission_of_quotation_view.xml',

    ],

}
