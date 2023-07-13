# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
#
{
    'name': "Multi Employee Login",
    'summary': """Multi Employee Login""",
    'description': """Multi Employee Login""",
    'version': "3.2",
    'category': "website",
    'author': "Kiran Infosoft",
    'website': "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    "depends": [
        'base',
        'sale',
        'purchase',
        'account',
        'mrp',
        'hr_expense',
        'stock_requestion',
        'nilar_purchase_requisition',
        'submission_of_quotation',
        'mrp_to_produce',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/res_users_view.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/mrp_production_view.xml',
        'views/stock_adjustment_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_scrap_view.xml',
        'views/account_move_views.xml',
        'views/hr_expense_views.xml',
        'views/stock_requestion_view.xml',
        'views/submission_quotation_view.xml',
        'views/mrp_to_produce_form_view.xml',
        'views/purchase_requisition_view.xml',
        'wizards/employee_login_wiz_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/multi_employee_login/static/src/js/employee_login.js',
            '/multi_employee_login/static/src/js/pos_employee_login.js',
        ]
    },
    'application': False,
    'installable': True,
}
