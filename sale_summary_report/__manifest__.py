{
    'name': 'Sale Summary Report',

    'category': 'sale',

    'description': """
    Sale, Purchase, Invoice and POS analysis report added multi uom and quantity.
    """,

    'author': 'Asia Matrix',

    'version': '2.0',

    'depends': [
        'sale_requisition',
    ],

    'data': [
        'security/ir.model.access.csv',
        'report/sale_summary_report.xml',
        'report/sale_report_extend.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
