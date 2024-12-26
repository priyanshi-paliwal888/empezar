{
    'name': 'Empezar Delivery Order',
    'summary': 'Empezar Delivery Order',
    'category': 'Empezar/Delivery',
    'version': '17.0.1.0.0',
    'depends': ['empezar_base', 'empezar_vessel_booking'],
    'author': 'Codetrade.io',
    'website': 'https://www.codetrade.io/',
    'license': 'LGPL-3',
    'description': """Empezar Delivery Order""",
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/delivery_order_view.xml",
        "views/view_allocation_details.xml",
        "wizard/update_allocation_wizard.xml",
    ],
    'installable': True,
    'application': True,
    "assets": {
        "web.assets_backend": [
            "empezar_delivery_order/static/src/css/**/*",
            "empezar_delivery_order/static/src/images/**/*",
            "empezar_delivery_order/static/src/js/**/*",
            "empezar_delivery_order/static/src/xml/**/*",
        ],
    },
}
