{
    'name': 'Course Catalog',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Manage courses and student enrollments.',
    'author': 'Developer',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        # BUG B2 FIX: removed 'security/groups.xml' — file did not exist,
        # causing FileNotFoundError on every install attempt.
        'views/course_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}