# -*- coding: utf-8 -*-
{
    'name': "Car Way",

    'summary': """For Car Delivery Way """,

    'description': """
        For Car Delivery Way
    """,

    'author': "Asiamatrix",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'Extratools',

    'version': '4.8',

    'license': "LGPL-3",

    'depends': [
        'mail',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/car_way_form_view.xml',
        'views/car_way_name_view.xml',
        'views/stock_picking_view.xml',
        'views/account_analytic_views.xml',
        'wizards/car_way_wizard_views.xml',
        'wizards/car_way_branch_view.xml',
        'data/sequence.xml',
        'report/report.xml',
        'report/car_way_total_report_view.xml',
    ],

    'installable': True,
    'application': False,
}
