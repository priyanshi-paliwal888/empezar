# -*- coding: utf-8 -*-
{
    'name': 'Empezar CMS EDI',
    'version': '17.0.1.0.0',
    'summary': 'Implement a EDI send functionality for CMS',
    'description': 'Implement a EDI send functionality for CMS',
    "category": "Empezar/Edi",
    'website': 'https://www.codetrade.io/',
    'author': 'Codetrade.io',
    'license': 'LGPL-3',
    'depends': ['empezar_base','empezar_move_in','empezar_move_out'],
    'data': [
        "data/edi_sequences.xml",
        "security/ir.model.access.csv",
        "views/edi_setting_views.xml",
        "views/edi_logs_views.xml",
    ],
    'installable': True,
    'application': True,
    "assets": {
            "web.assets_backend": [
                "empezar_edi/static/css/**/*",

            ],
        },
}
