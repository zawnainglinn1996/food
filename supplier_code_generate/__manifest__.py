# -*- coding: utf-8 -*-
{
    'name': "Supplier Code Generation",

    'summary': """Added Supplier Code Generation""",

    'description': """
        Added Supplier Code Generation.
    """,

    'author': "Asia Matrix Software Solution",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Contact',

    'version': '1.4',

    'license': "LGPL-3",

    'depends': [
        'base',
        'base_customer_supplier',
    ],

    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'wizard/supplier_sequence.xml',
    ],

    'installable': True,

    'application': False,
}
