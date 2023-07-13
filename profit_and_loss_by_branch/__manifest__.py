# -*- coding: utf-8 -*-
{
    'name': 'Profit & Loss Excel Report',
    'version': '1.2',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'author': 'Asia Matrix',
    'depends': [
        'report_xlsx',
        'account',

    ],
    'data': [
        'security/ir.model.access.csv',
        'report/profit_losss_report.xml',
        'wizard/profit_loss_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
