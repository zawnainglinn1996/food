# -*- coding: utf-8 -*-

{
    "name": "Zawgyi font in Report",
    'summary': 'Zawgyi Font in QWeb Report',
    "description":
        """
        Odoo Zawgyi font Web Report Myanmar.
        """,
    'category': 'web',
    'version': '1.1',
    'author': "TechnoSquare",
    'website': 'http://technosquare.in/',
    "support": "info@technosquare.in",
    
    "depends": ['web'],
    'data': [],
    'assets': {

        'web.report_assets_common': [
            'zawgyi_font/static/src/css/stylesheet.css',

        ],
        'web.report_assets_pdf': [
            'zawgyi_font/static/src/css/stylesheet.css',
        ]

    },
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
}