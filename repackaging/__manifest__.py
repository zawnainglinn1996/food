{
    'name':
    'Repackaging',
    'version':
    '2.1',
    'category':
    'inventory',
    'summary':
    'Repackaging for stocks',
    'email':
    'asiamatrix.dev@gmail.com',
    'author':
    'asiamatrix',
    'company':
    'Asia Matrix Co., Ltd',
    'description':
    """
This module is the repackaging for the stocks in the inventory operation.
    """,
    'depends': [
        'stock',
        'stock_account',
        'analytic_account',
        'report_py3o',
    ],
    'data': [
        'data/repackaging_sequence_data.xml',
        'security/ir.model.access.csv',
        # 'report/repackaging_report_template.xml',
        'report/repackaging_report.xml',
        'views/stock_repackaging_data.xml',
        'views/product_view.xml',
        'views/stock_location_view.xml',
    ],
    'installable':
    True,
    'auto_install':
    False,
}
