
{
    'name': 'Inventory Activities Report',
    'version': '2.2',
    'summary': "Inventory  Activities Report",
    'description': "Inventory  Activities Report",
    'category': 'Manufacture',
    'depends': [
        'mrp',
        'stock',
        'multi_uom',
        'report_xlsx',
                ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/inventory_activities_report_views.xml',
        'wizards/inventory_activities_cost_reports_views.xml',
        'wizards/production_sav_report_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'auto_install': False,
}
