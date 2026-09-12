# Changelog

All notable changes to the `sterrenboom` addon. Versions follow the Odoo manifest
convention `19.0.<major>.<minor>.<patch>`.

## [19.0.2.0.0] — 2026-09-12

Publishes the *Halloweentocht – Trick or Treat* event (Friday 23 October 2026) through
the Odoo Events app, with a custom website page that shows the flyer information and
lets visitors register. Requires a module upgrade and installs `website_event`.

### Added
- Dependency on `website_event` (Odoo Events + Website).
- Event data (`data/event_halloweentocht_data.xml`, `noupdate`): the event, the
  location partner *Kerk van Wortegem*, the partner *Ferm Wortegem* and two tickets
  (*Volwassene* € 12, *Kind* € 10) that close on 16 October 2026 23:59.
- `event.event.sterrenboom_page_view_id` (*Custom Website Page*): a QWeb template
  rendered instead of the standard event page. The `/event/<slug>/register` route is
  overridden to serve it; the standard ticket modal and attendee form keep working.
- `event.event.ticket.sterrenboom_price` (*Price (€)*), shown on the custom page and in
  the standard registration modal, with a non-negative check constraint.
- Website template `sterrenboom.event_page_halloweentocht` with a Halloween theme
  (`static/src/scss/event_halloweentocht.scss`): programme, prices, location,
  calendar links and the registration button.
- Tests for the event data and for the custom / standard page routing.

### Changed
- *Sterrenboom / User* now implies *Events / User* and *Sterrenboom / Manager* implies
  *Events / Administrator*, so committee members can follow up website registrations.

## [19.0.1.0.0] — 2026-09-12

Migrated the module to Odoo 19 and turned the repository into a deployable addons path.

### Added
- Security groups (*Sterrenboom / User* and *Sterrenboom / Manager*) under a
  `res.groups.privilege`, replacing blanket `base.group_user` access.
- Event fields `date_end`, `active` and stored `attendee_count`; member field
  `event_ids` with computed `event_count`.
- Event status buttons and a date-consistency constraint.
- Calendar and search views for events, search view for members.
- Demo data, and a test suite covering constraints, the status workflow and computes.
- Module icon, CI (ruff, pylint-odoo, install + upgrade + tests on Odoo 19.0),
  pre-commit hooks, local Docker stack, `.gitignore`/`.gitattributes`/`.editorconfig`.

### Changed
- Repository restructured: the addon now lives in `sterrenboom/` at the repo root, so
  the repository root can be used as an addons path without renaming the clone.
- Views updated for Odoo 19: `<list>` instead of `<tree>`, `<chatter/>` instead of the
  `oe_chatter` div, `view_mode="list,form"`.
- Unique email moved from `_sql_constraints` to `models.Constraint`.
- `models/sterrenboom_model.py` split into `sterrenboom_member.py` and
  `sterrenboom_event.py`; views split per model.
- Event `description` and `notes` are now `Html` instead of `Text`.

### Removed
- Stray `sterrenboom/mnt/user-data/outputs/` directory committed by accident.
