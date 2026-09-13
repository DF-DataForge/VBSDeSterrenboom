{
    'name': 'Sterrenboom Parent Committee',
    'version': '19.0.4.0.0',
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
* Website registrations that confirm a sales order, post its customer invoice and
  mail the attendee bank transfer instructions with a structured communication and
  a SEPA credit transfer QR code, so the payment reconciles itself in Accounting
""",
    'author': 'Data Forge',
    'maintainer': 'Data Forge',
    'website': 'https://github.com/DF-DataForge/VBSDeSterrenboom',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account_qr_code_sepa',
        'event_sale',
        'l10n_be',
        'website_event',
        'website_event_sale',
    ],
    'data': [
        'security/sterrenboom_groups.xml',
        'security/ir.model.access.csv',
        'views/sterrenboom_member_views.xml',
        'views/sterrenboom_event_views.xml',
        'views/sterrenboom_menus.xml',
        'views/event_event_views.xml',
        'views/sale_order_views.xml',
        'views/event_templates.xml',
        'views/event_halloweentocht_templates.xml',
        'data/mail_template_data.xml',
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
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
}
