# -*- coding: utf-8 -*-
{
    'name': "Manufacturing To Produce",

    'summary': """For MRP TO PRODUCE""",

    'description': """
        For MRP TO PRODUCE 
    """,

    'author': "Asia Matrix",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Manufacturing',

    'version': '2.2',

    'license': "LGPL-3",

    'depends': [
       'mrp',
        'multi_uom',
    ],

    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/mrp_production_view.xml',
        'views/mrp_produce_views.xml',
    ],

    'installable': True,
    'application': False,
}
