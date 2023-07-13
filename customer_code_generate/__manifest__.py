# -*- coding: utf-8 -*-
{
    'name': "Customer Code Generation",

    'summary': """Added Customer Code Generation""",

    'description': """
        Added Customer Code Generation.
    """,

    'author': "Asia Matrix Software Solution",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Contact',

    'version': '1.4',
    'license': "LGPL-3",

    'depends': [
        'base',
        'base_customer_supplier',
        'sequence_reset_period',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/res_partner_views.xml',
        'wizard/customer_sequence.xml',
    ],

    'installable': True,
    'license': "LGPL-3",
    'application': False,
}