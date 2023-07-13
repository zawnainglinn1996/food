# -*- coding: utf-8 -*-
{
    'name': 'Stock Details  Report (By Locations)',
    'version': '1.8',
    'summary': 'Stock Details  Report (By Locations)',
    'sequence': 101,
    'category': 'Inventory',
    'website': 'https://www.asiamatrixsoftware.com',
    'depends': [
        'sale_stock',
        'purchase_stock',
        'report_xlsx',
        'stock_backdate_report'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_in_out_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
