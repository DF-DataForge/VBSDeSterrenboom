# Changelog

All notable changes to the `sterrenboom` addon. Versions follow the Odoo manifest
convention `19.0.<major>.<minor>.<patch>`.

## [19.0.3.0.0] — 2026-09-12

Website registrations now produce a confirmed sales order and a posted customer invoice,
so the attendee gets bank transfer instructions with a structured communication and
Accounting reconciles the payment on its own. Requires a module upgrade; the upgrade
installs `event_sale`, `website_event_sale`, `account_qr_code_sepa` and `l10n_be`.

### Added
- Confirming the attendee form no longer sends the visitor to the eCommerce checkout:
  the order is confirmed and invoiced, and the confirmation page shows the amount, the
  IBAN, the **structured communication** and a scannable **SEPA credit transfer QR-code**
  (the same one Odoo prints on an invoice PDF).
- `sterrenboom.mail_template_registration_payment`: the attendees are mailed the same
  payment instructions, with a portal link to the invoice.
- `sale.order._sterrenboom_invoice_registrations()`, `account.move._sterrenboom_payment_values()`
  / `_sterrenboom_payment_qr_code()` and `event.registration._sterrenboom_payment_values()`
  / `_sterrenboom_send_payment_instructions()`.
- Install/upgrade hook that puts sale journals of a Belgian company on the
  `+++000/0000/00000+++` communication standard when they still use Odoo's default.

### Fixed
- The payment-instructions mail template compared the due date with an unset invoice
  date, which made the module upgrade fail on databases that already hold a draft
  invoice (Odoo validates a mail template against an existing record when saving it).

### Changed
- Ticket prices moved from `event.event.ticket.sterrenboom_price` to the standard
  `price` field from `event_sale`, so the website, the sales order and the invoice all
  quote the same amount. A migration copies existing values across; check
  **Events → Halloweentocht → Tickets** after upgrading.
- The Halloweentocht page no longer repeats the ticket description under each ticket
  name, and explains that the payment details arrive on screen and by mail.
- The Halloweentocht page hides the website navigation bar, so only the event is shown.
- The page uses `static/src/img/halloweentocht.png` as its header when that file is
  present, and falls back to the typographic title while it is not.

### Fixed
- The Halloweentocht title overflowed the screen on a phone: the hero title, subtitle,
  date badge, panels and ticket rows now scale with the viewport instead of using fixed
  heading sizes.

### Removed
- `event.event.ticket.sterrenboom_price` and its views, superseded by `price`.

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

### Fixed
- Member and event search views failed Odoo 19 view validation (`expand`/`string`
  on the group-by `<group>`), which blocked installing the module.
- `attendee_count` relabelled *Attendee Count* to stop the duplicate-label warning.

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
