# -*- coding: utf-8 -*-
{
    'name': "Manufacturing To Journal",

    'summary': """For MO TO Journal""",

    'description': """
        For Sale Requisition 
    """,

    'author': "Asia Matrix",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Manufacturing',

    'version': '4.2',

    'license': "LGPL-3",

    'depends': [
       'mrp'
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/mrp_access.xml',
        'views/mrp_production_view.xml',
        'views/res_confign_setting_view.xml',
    ],

    'installable': True,
    'application': False,
}
