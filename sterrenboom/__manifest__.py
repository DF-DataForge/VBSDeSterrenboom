{
    'name': 'Sterrenboom Parent Committee',
    'version': '19.0.1.0.0',
    'category': 'Services/Sterrenboom',
    'summary': 'Manage parent committee members and events for VBS De Sterrenboom',
    'description': """
Sterrenboom Parent Committee
============================

Tools for managing the parent committee (oudercomité) of VBS De Sterrenboom:

* Member register with committee roles and contact details
* Event planning with attendee tracking and a status workflow
* Chatter and scheduled activities on both members and events
""",
    'author': 'Data Forge',
    'maintainer': 'Data Forge',
    'website': 'https://github.com/DF-DataForge/VBSDeSterrenboom',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/sterrenboom_groups.xml',
        'security/ir.model.access.csv',
        'views/sterrenboom_member_views.xml',
        'views/sterrenboom_event_views.xml',
        'views/sterrenboom_menus.xml',
    ],
    'demo': [
        'demo/sterrenboom_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
