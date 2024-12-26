{
    'name': 'Image Capture Widget',
    'version': '17.0.1.0.0',
    'category': 'Empezar',
    'sequence': '20',
    'summary': 'Image Capture Widget for Image Field. '
               'This module allows to capture the users image from the webcam.',
    'author': 'Codetrade.io',
    'website': 'https://www.codetrade.io/',
    'description': "This module is used to add Image Capture Widget for Image "
                   "Field. We can capture the image from the webcam and "
                   "upload into the binary field",
    'depends': ['sale_management', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            '/image_capture_upload_widget/static/src/js/image_capture.js',
            '/image_capture_upload_widget/static/src/xml/image_capture_templates.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
