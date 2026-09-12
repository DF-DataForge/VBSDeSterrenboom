# __manifest__.py
{
    'name': 'Sterrenboom Parent Committee',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Module for managing sterrenboom parent committee activities',
    'description': """
        This module provides tools for managing parent committee (oudercomité) activities
        for sterrenboom, including event management, communications, and member tracking.
    """,
    'author': 'Data Forge',
    'website': 'https://github.com/DF-DataForge/VBSDeSterrenboom',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/sterrenboom_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
