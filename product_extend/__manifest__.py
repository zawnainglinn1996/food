# -*- coding: utf-8 -*-
{
    'name': "Product Brand",

    'summary': """Product Brand""",

    'description': """
        1.For Product Brand
    """,

    'author': "nevermore",
    'website': "asiamatrixsoftware.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '1.8',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'stock',

    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_view.xml',
        'views/product_family_view.xml',
        'views/product_group_view.xml',
        'views/product_extend_view.xml',

    ],

}
