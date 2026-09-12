# Changelog

All notable changes to the `sterrenboom` addon. Versions follow the Odoo manifest
convention `19.0.<major>.<minor>.<patch>`.

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
