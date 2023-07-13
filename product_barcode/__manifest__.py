{
    'name': 'Product Barcode Generator',
    'version': '1.2',
    'summary': 'Generates EAN13 Standard Barcode for Product.',
    'category': 'Inventory',
    'author': 'Asia Matrix',
    'maintainer': 'Asiamatrix ',
    'company': 'Asia Matrix Software Soluction',
    'website': 'www.asiamatrixsoftware.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/product_view.xml',
        'views/product_view.xml'

    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
