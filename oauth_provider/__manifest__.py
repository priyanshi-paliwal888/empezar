# -*- coding: utf-8 -*-
{
    'name':"OAuth Provider",
    'summary':"Allows to use Odoo as an OAuth2 provider",
    'version': '17.0.1.0.0',
    'category': 'Empezar/Authentication',
    'website': 'http://www.syleam.fr/',
    'author': 'SYLEAM, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'external_dependencies': {
        'python': ['oauthlib'],
    },
    'depends': ['base','web','website'],
    'data': [
        'security/oauth_provider_security.xml',
        'security/ir.model.access.csv',
        'views/oauth_provider_client.xml',
        'views/oauth_provider_scope.xml',
        'templates/authorization.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
}
