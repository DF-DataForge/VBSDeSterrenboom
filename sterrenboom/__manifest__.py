{
    'name': 'Sterrenboom Parent Committee',
    'version': '19.0.2.0.0',
    'category': 'Services/Sterrenboom',
    'summary': 'Manage parent committee members and events for VBS De Sterrenboom',
    'description': """
Sterrenboom Parent Committee
============================

Tools for managing the parent committee (oudercomité) of VBS De Sterrenboom:

* Member register with committee roles and contact details
* Event planning with attendee tracking and a status workflow
* Chatter and scheduled activities on both members and events
* Custom website pages for events published through the Odoo Events app,
  including the "Halloweentocht - Trick or Treat" event
""",
    'author': 'Data Forge',
    'maintainer': 'Data Forge',
    'website': 'https://github.com/DF-DataForge/VBSDeSterrenboom',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'website_event',
    ],
    'data': [
        'security/sterrenboom_groups.xml',
        'security/ir.model.access.csv',
        'views/sterrenboom_member_views.xml',
        'views/sterrenboom_event_views.xml',
        'views/sterrenboom_menus.xml',
        'views/event_event_views.xml',
        'views/event_ticket_views.xml',
        'views/event_templates.xml',
        'views/event_halloweentocht_templates.xml',
        'data/event_halloweentocht_data.xml',
    ],
    'demo': [
        'demo/sterrenboom_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sterrenboom/static/src/scss/event_halloweentocht.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
