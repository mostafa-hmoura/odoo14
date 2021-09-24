{
    'name' : 'Public Market',
    'version' : '14.0.0',
    'summary': 'Public Market',
    'sequence': -10,
    'description': """ Public Market Model""",
    'category': 'Productivity',
    'website': 'test.com',
    'images' : [],
    'depends' : ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/default_value.xml',
        'views/public_market_views.xml',
        'views/template_attachement_views.xml',
        'views/attachement_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
