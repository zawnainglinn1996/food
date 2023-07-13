# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Custom Product Labels',
    'version': '1.7',
    'category': 'Inventory',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz',
    'license': 'LGPL-3',
    'summary': 'Print custom product labels with barcode and for shelve tab',
    'images': ['static/description/banner.png'],
    'live_test_url': 'https://garazd.biz/r/1Jw',
    'depends': [
        'product', 'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/barcode_report_nilar.xml',
        'report/product_label_reports.xml',
        'report/product_label_templates.xml',
        'report/product_label_template_19x32.xml',
        'wizard/print_product_label_views.xml',
        'report/product_label_template_shelvetab.xml',
        'views/product_views_extend.xml'
    ],
    'demo': [
        'demo/product_demo.xml',
    ],
    'external_dependencies': {
    },
    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
