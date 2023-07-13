{
    'name': 'POS Slip Design',
    'summary': """POS Receipt Design""",
    'version': '3.9',
    'description': """POS Receipt Design""",
    'author': 'Asia Matrix',
    'company': 'Asia Matrix',
    'website': 'www.asiamatrixsoftware.com',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale','promotion_program'],
    'license': 'LGPL-3',
    'data': [
        'data/pos_order_sequence.xml',
        'views/pos_config_views.xml',
        'reports/reports.xml',
    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'point_of_sale.assets': [
            'pos_slip_extend/static/src/js/*',
        ],
        'web.assets_qweb': [
            'pos_slip_extend/static/src/xml/pos_slip_extend.xml',
            'pos_slip_extend/static/src/xml/ProductItemExtend.xml',
            'pos_slip_extend/static/src/xml/OrderlineExtend.xml',
            'pos_slip_extend/static/src/xml/ReceiptScreenExtend.xml',
            'pos_slip_extend/static/src/xml/TableNoButton.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
