# -*- coding: utf-8 -*-
{
    'name': 'Sale Detail Report',
    'version': '1.5',
    'sequence': 100,
    'category': 'Sale',
    'website': 'https://www.asiamatrixsoftware.com',
    'author': 'Asia Matrix',
    'depends': [
        'report_xlsx',
        'sale',

    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/sale_analysis_report.xml',
        'reports/pos_analysis_report.xml',
        'wizard/sale_detail_report.xml',
        'wizard/pos_analysis_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
