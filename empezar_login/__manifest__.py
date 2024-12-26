{
    'name' : 'Empezar Login Page',
    'summary': 'Empezar Login',
    'category' : 'Empezar/Login',
    'version': '17.0.1.0.0',
    'depends' : ['web','auth_signup'],
    'author': 'Codetrade.io',
    'website': 'https://www.codetrade.io/',
    'license': 'LGPL-3',
    'description': """Empezar Login""",
    "data": [
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_frontend': [
            'empezar_login/static/src/css/login_page.scss',
            'empezar_login/static/src/js/login_page.js',
        ],
    },
}
