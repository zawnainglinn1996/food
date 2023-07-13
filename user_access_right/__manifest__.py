# -*- coding: utf-8 -*-
{
    'name': "User Access Right",

    'summary': """Access Right Module""",

    'description': """
        This Module Add user access right.
    """,

    'author': "Asia Matrix Software Solution",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Security',

    'version': '0.8',

    'license': 'LGPL-3',

    'depends': [
        'multi_employee_login',
        'stock_account',
        'stock_requestion',
        'point_of_sale',
        'base',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/inventory_access_views.xml',
        'security/point_of_sale_security.xml',
        'security/product_cost_access.xml',
        'views/hr_access_views.xml',
        'views/stock_views.xml',
        'views/point_of_sale_views.xml',
        'views/vendor_pricelist_views.xml',
        'views/product_views.xml',

    ],

    'images': ['static/description/icon.png'],
}