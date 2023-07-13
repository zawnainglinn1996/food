# -*- coding: utf-8 -*-
{
    'name': "Stock Requestion",

    'summary': """Stock Requestion""",

    'description': """
        1.For Stock Requestion
    """,

    'author': "asiamatrix",
    'website': "http://www.blue-stone.net",
    'category': 'stock',
    'version': '5.3',
    'license': "LGPL-3",

    'depends': [
        'stock',
        'base',

    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/stock_requestion_view.xml',
        'views/stock_picking_view.xml',
        'views/res_company_form_view.xml',


    ],
    'assets': {
        'web.assets_backend': [
            'stock_requestion/static/src/js/qty_at_date_widget.js',
        ],
        'web.assets_qweb': [
            'stock_requestion/static/src/xml/qty_at_date.xml',
        ],
    },

}
