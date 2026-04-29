{
    'name': 'Real Estate — Accounting',
    'version': '16.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Generates customer invoices when a property is sold.',
    'description': (
        'When a property is marked as Sold, automatically creates a '
        'draft customer invoice with a 6%% commission and a fixed '
        'EUR 100 administrative fee.'
    ),
    'author': 'Developer',
    'depends': ['estate', 'account'],
    'data': [
        'views/estate_property_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}