{
    'name': 'Real Estate',
    'version': '16.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Real Estate Property Management',
    'description': 'Manage properties, offers, and sales through the full lifecycle.',
    'author': 'Developer',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/inherited_views.xml',
        'views/estate_menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}