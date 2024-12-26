{
    'name': 'Empezar Dashboards',
    'summary': 'Empezar Dashboards',
    'category': 'Empezar/Dashboards',
    'version': '17.0.1.0.0',
    'depends': ['base', 'web'],
    'author': 'Codetrade.io',
    'website': 'https://www.codetrade.io/',
    'license': 'LGPL-3',
    'description': """Empezar Dashboards""",
    "data": [
        'views/dashboards_views.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'empezar_dashboards/static/src/lib/chart_min.js',
            'empezar_dashboards/static/src/lib/moment_min.js',
            'empezar_dashboards/static/src/lib/datepicker_min.js',
            'empezar_dashboards/static/src/lib/datepicker_min.css',
            'empezar_dashboards/static/src/components/**/*.js',
            'empezar_dashboards/static/src/components/**/*.xml',
            'empezar_dashboards/static/src/components/**/*.scss',
        ],
    },
}
