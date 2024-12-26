{
    'name': 'Empezar Reports',
    'summary': 'Module for managing reports.',
    'category': 'Empezar/Reports',
    'version': '17.0.1.0.0',
    'depends': ['empezar_base', 'empezar_move_in','empezar_move_out','empezar_inventory','empezar_repair','empezar_account_invoices'],
    'author': 'Codetrade.io',
    'website': 'https://www.codetrade.io/',
    'license': 'LGPL-3',
    "data": [
        'security/ir.model.access.csv',
        'views/movement_and_inventory_reports.xml',
        'views/repair_reports.xml',
    ],
    'installable': True,
    'application': True,
}
