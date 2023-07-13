{
    'name': 'POS Counter Control',
    'version': '0.7',
    'author': 'Asia Matrix',
    'category': 'Point of Sale',
    'depends': ['point_of_sale','hr'],
    'license': "LGPL-3",
    'data': [
        'security/ir.model.access.csv',
        # 'security/record_rules.xml',
        'views/hr_employee_form_view.xml',
        'views/pos_location_form_view.xml',
        'views/pos_conf_extend_view.xml',
        'views/pos_dashboard_view.xml',
        'views/pos_view.xml',
    ],
    'license': 'OPL-1',
}
