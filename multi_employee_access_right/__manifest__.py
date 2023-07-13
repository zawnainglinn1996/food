# -*- coding: utf-8 -*-
{
    'name': "Multi Employee Access Right",

    'summary': """Access Right Module""",

    'description': """
        This Module Add user access right.
    """,

    'author': "AsiaMatrix",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Security',

    'version': '1.6',

    'license': 'LGPL-3',

    'depends': [
        'hr',
        'user_access_right',
        'base',
    ],

    'data': [

        'views/hr_employee_form_view.xml',

    ],

    'images': ['static/description/icon.png'],
}