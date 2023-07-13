{
    'name': 'Kitchen POS Slip Design',
    'summary': """Kitchen POS Receipt Design""",
    'version': '1.1',
    'description': """Kitchen POS Receipt Design""",
    'author': 'ETK',
    'company': 'Asia Matrix',
    'website': 'www.asiamatrixsoftware.com',
    'category': 'Point of Sale',
    'depends': ['pos_restaurant',
                'point_of_sale'],
    'license': 'LGPL-3',
    'data': [

    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'point_of_sale.assets': [
            'kitchen_pos_receipt/static/src/js/kitchen_pos_receipt.js',
        ],
        'web.assets_qweb': [
            'kitchen_pos_receipt/static/src/xml/kitchen_pos_slip.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
