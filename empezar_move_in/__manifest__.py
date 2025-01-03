{
    'name' : 'Empezar Move In',
    'summary': 'Empezar Move In',
    'category' : 'Empezar/Move In',
    'version': '17.0.1.0.0',
    'depends' : ['empezar_base', 'empezar_delivery_order', 'empezar_vessel_booking', 'empezar_inventory'],
    'author': 'Codetrade.io',
    'website': 'https://www.codetrade.io/',
    'license': 'LGPL-3',
    'description': """Empezar Move in process""",
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/gate_pass_mi_data.xml",
        "views/empezar_move_in_views.xml",
        'reports/external_layout_inherit.xml',
        'reports/move_in_report.xml',
        'reports/move_in_report_action.xml',
        'views/container_facilities_views.xml',
    ],
    'installable': True,
    'application': True,
    "assets": {
        "web.assets_backend": [
            "empezar_move_in/static/src/xml/**/*",
            "empezar_move_in/static/src/js/**/*",
            "empezar_move_in/static/src/css/**/*",
        ],
    },
}
