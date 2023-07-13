# -*- coding: utf-8 -*-
{
    'name': "Sale Extend",

    'summary': """For Sale Module Customization""",

    'description': """
        For Sale Module Customization
    """,

    'author': "Asia Matrix Software Solution",

    'website': "http://www.asiamatrixsoftware.com",

    'category': 'sale',

    'version': '3.5',

    'license': "LGPL-3",

    'depends': [
        'sale',
        'analytic_account',
        'sale_stock',
        'sales_team',
        'multi_employee_access_right',
    ],

    'data': [
        'views/sale_order_form_view.xml',
        'views/analytic_account_form_view.xml',
        'views/crm_team_view.xml',
        'report/sale_analysis_report.xml',
        'security/hide_tax_access.xml',
        'data/sequence.xml',
    ],

    'installable': True,
    'application': False,
}
