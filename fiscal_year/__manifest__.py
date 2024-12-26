# -*- coding: utf-8 -*-
{
    'name': 'Odoo 17 Fiscal Year & Lock Date',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Odoo 17 Fiscal Year, Fiscal Year in Odoo 17, Lock Date in Odoo 17',
    'description': 'Odoo 17 Fiscal Year, Fiscal Year in Odoo 17',
    'website': 'https://www.codetrade.io/',
    'author': 'Codetrade.io',
    'license': 'LGPL-3',
    'depends': ['account','empezar_base'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'wizard/change_lock_date.xml',
        'views/fiscal_year.xml',
        'views/settings.xml',
    ],
    'installable': True,
}
