# -*- coding: utf-8 -*-
{
    'name': "Res Partner Extend",

    'summary': """
        Res Partner Extend""",

    'description': """
        Res Partner Extend
    """,

    'author': "Asiamatrix",
    'website': "http://www.asiamatrixsoftware.com",
    'category': 'Partner',
    'version': '1.2',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_customer_supplier'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml'
    ],
    'installable': True,
    'application': False,
}
