# VBS De Sterrenboom — Parent Committee

[![CI](https://github.com/DF-DataForge/VBSDeSterrenboom/actions/workflows/ci.yml/badge.svg)](https://github.com/DF-DataForge/VBSDeSterrenboom/actions/workflows/ci.yml)
[![Odoo](https://img.shields.io/badge/Odoo-19.0-875A7B)](https://www.odoo.com/documentation/19.0/)
[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue)](LICENSE)

Odoo 19 addon for managing the parent committee (oudercomité) of VBS De Sterrenboom:
a member register with committee roles, event planning with attendee tracking,
a status workflow, chatter and scheduled activities, and custom website pages for
events published through the Odoo Events app (currently the *Halloweentocht*).

## Repository layout

This repository **is an Odoo addons path**. The addon lives in a folder named after its
technical name, so the repo can be cloned straight onto a server without renaming anything.

```
VBSDeSterrenboom/            <- add THIS folder to addons_path
├── sterrenboom/             <- the addon (technical name: sterrenboom)
│   ├── __manifest__.py
│   ├── hooks.py                    <- install-time accounting configuration
│   ├── controllers/
│   │   └── main.py                 <- custom event page + the registration flow
│   ├── models/
│   │   ├── sterrenboom_member.py
│   │   ├── sterrenboom_event.py
│   │   ├── event_event.py          <- event.event: Custom Website Page
│   │   ├── event_registration.py   <- registration -> invoice + payment mail
│   │   ├── sale_order.py           <- confirm + invoice a registration order
│   │   └── account_move.py         <- IBAN, communication and SEPA QR-code
│   ├── views/
│   │   ├── sterrenboom_member_views.xml
│   │   ├── sterrenboom_event_views.xml
│   │   ├── sterrenboom_menus.xml
│   │   ├── event_event_views.xml
│   │   ├── event_templates.xml                <- confirmation page payment panel
│   │   └── event_halloweentocht_templates.xml <- the Halloweentocht web page
│   ├── data/
│   │   ├── mail_template_data.xml             <- payment instructions mail
│   │   └── event_halloweentocht_data.xml      <- the event, its tickets and location
│   ├── migrations/                 <- upgrade scripts per manifest version
│   ├── security/
│   │   ├── sterrenboom_groups.xml
│   │   └── ir.model.access.csv
│   ├── static/src/scss/event_halloweentocht.scss
│   ├── demo/
│   ├── tests/
│   └── static/description/icon.png
├── .github/workflows/ci.yml  <- lints + installs the module on Odoo 19
├── docker-compose.yml        <- local Odoo 19 stack
└── pyproject.toml            <- ruff + pylint-odoo config
```

## Deployment on CloudPepper

CloudPepper pulls this repository into the server's custom addons directory and adds
the **repository root** to `addons_path`.

1. In CloudPepper, open your Odoo 19 instance → **Git Repositories** (or *Custom Modules*).
2. Add the repository:
   - URL: `https://github.com/DF-DataForge/VBSDeSterrenboom.git`
   - Branch: `main`
   - For a private repo, use a GitHub deploy key or a fine-grained PAT with read-only
     `Contents` access. Never commit that token to this repo.
3. Pull the repository, then **restart the Odoo service** so the new addons path is scanned.
4. In Odoo: **Apps → Update Apps List**, search for *Sterrenboom*, click **Install**.

To ship an update: merge to `main`, pull the repo in CloudPepper, restart Odoo, then
**Apps → Sterrenboom → Upgrade**.

> Verify that CloudPepper's addons path points at the repository root, not at the
> `sterrenboom/` folder inside it. Pointing it one level too deep makes Odoo see the
> module's subfolders as addons and the module will not appear in the Apps list.

## Local development

Requires Docker. No local Python or Odoo install needed.

```bash
docker compose up -d
```

Open <http://localhost:8069>, create a database, and install the *Sterrenboom* app.
The repo is mounted read-only at `/mnt/extra-addons`, so edits on your machine are picked
up by restarting the container:

```bash
docker compose restart odoo
```

To install the module with demo data and run its test suite exactly as CI does:

```bash
docker compose run --rm --no-deps odoo odoo --db_host=db --db_user=odoo --db_password=odoo -d dev --init sterrenboom --test-enable --test-tags=/sterrenboom --stop-after-init --no-http
```

## Code quality

`pre-commit` runs ruff (lint) and `pylint-odoo` with Odoo 19 checks enabled:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The same hooks run in CI on every push and pull request, alongside a job that installs
the module on a clean Odoo 19.0 container and runs its tests.

## Models

### `sterrenboom.member`

| Field | Type | Notes |
| --- | --- | --- |
| `name` | Char | Required, tracked |
| `email` | Char | Tracked, unique across members |
| `phone` | Char | |
| `role` | Selection | Chairman / Treasurer / Secretary / Member |
| `active` | Boolean | Archive instead of deleting |
| `event_ids` | Many2many | Events attended |
| `event_count` | Integer | Computed |

### `sterrenboom.event`

| Field | Type | Notes |
| --- | --- | --- |
| `name` | Char | Required, tracked |
| `date` / `date_end` | Datetime | Start required; end must not precede start |
| `location` | Char | |
| `description` / `notes` | Html | Notes are internal |
| `member_ids` | Many2many | Attendees |
| `attendee_count` | Integer | Computed, stored |
| `state` | Selection | Planned → Ongoing → Completed, or Cancelled |

Both models inherit `mail.thread` and `mail.activity.mixin`, so they have chatter,
followers and scheduled activities.

### Extensions of the Odoo Events app

The module depends on `website_event` and extends it:

| Model | Field | Notes |
| --- | --- | --- |
| `event.event` | `sterrenboom_page_view_id` | *Custom Website Page*: a QWeb template rendered instead of the standard event page |

Ticket prices are the standard `event.event.ticket.price` from `event_sale`, so the
same number ends up on the website, on the sales order and on the invoice.

When an event has a custom page, opening its website URL (`/event/<slug>`) renders that
template with the same context as the standard page. The template wraps
`website_event.layout`, so the standard ticket modal, attendee form and confirmation
page are reused; only the presentation is custom. Events without a custom page are
untouched.

## Registration and payment flow

Registrations are paid by bank transfer, never on the website. After a visitor fills in
the attendee details and confirms:

1. `website_event_sale` puts the tickets in a sales order and creates one registration
   per attendee, linked to their order line.
2. `sale.order._sterrenboom_invoice_registrations()` puts the tickets **on hold**
   (`sterrenboom_tickets_on_hold`), confirms the order, creates its customer invoice and
   posts it. Posting is what generates the **structured communication**
   (`payment_reference`) and makes the receivable visible to Accounting. Confirming an
   order normally registers the attendees at once, which mails them their tickets; the
   hold keeps them *Unconfirmed* (`event.registration._compute_registration_status`) so
   no ticket goes out yet.
3. The visitor is redirected to the standard confirmation page, which shows the amount,
   the IBAN, the structured communication and a **SEPA credit transfer QR-code** — the
   same QR-code Odoo prints on an invoice PDF, so any banking app can scan it. There is
   no ticket download: the page says the tickets follow once the payment is processed.
4. The attendees are mailed the same instructions
   (`sterrenboom.mail_template_registration_payment`), with the note that the tickets
   follow once the payment is processed. The mail does not mention the invoice.
5. When the transfer arrives, the bank statement line carries the structured
   communication, so Accounting reconciles it against the invoice without manual
   matching. Nothing happens automatically after that: a committee member opens the
   sales order (**Sales → Orders**, or the invoice's *Source Document*) and clicks
   **Send Tickets**. That registers the attendees, which runs the event's *After each
   registration* communication — Odoo's confirmation mail with the ticket PDF — and
   records *Tickets Sent On* on the order. Events without such a communication get that
   mail sent directly.

### What the committee has to configure once

| Where | Setting |
| --- | --- |
| **Settings → Users & Companies → Companies** | a bank account with the committee's IBAN, and the company country set to Belgium. Mark the account as trusted (*Send Money*), otherwise Odoo strips it from the invoice when the public website posts it — the page and the mail still show the IBAN, but the invoice PDF will not |
| **Accounting → Configuration → Journals → Customer Invoices** | *Communication Standard* = `Belgium (+++000/2024/00182+++)`. The module sets this on install/upgrade for Belgian companies that still use Odoo's default |
| **Inventory/Sales → Products** | the ticket products must be *Invoiced on ordered quantities*, otherwise nothing is invoiceable at confirmation |
| Ticket taxes | the committee is normally not VAT liable — leave *Customer Taxes* empty on the ticket products so the invoiced amount equals the ticket price |

Free tickets (price 0) keep the plain `website_event` behaviour: no order, no invoice,
no payment panel.

## Halloweentocht – Trick or Treat

`data/event_halloweentocht_data.xml` creates the event from the 2026 flyer once
(`noupdate`), so the committee can edit it afterwards in **Events** without an upgrade
reverting the changes:

| | |
| --- | --- |
| When | Friday 23 October 2026, 18:30 – 23:00 (Europe/Brussels); departures 18:30 – 20:00, family party from 19:30 |
| Where | Kerk van Wortegem, 9790 Wortegem-Petegem |
| Tickets | *Volwassene* € 12, *Kind* € 10; registrations close 16 October 2026 at 23:59 |
| Website | published, custom page `sterrenboom.event_page_halloweentocht` |

The flyer does not mention an end time or a street address; both can be adjusted on the
event record. Payment is not collected on the website: confirming a registration creates
the sales order and the invoice, and the attendee transfers the amount with the
structured communication they get on screen and by mail.

### Flyer header image

The page opens with the flyer artwork, **`sterrenboom/static/src/img/halloweentocht.jpg`**,
a 1600 px wide JPEG made from `Header halloweentocht.png` in the repository root (the
original is too large to serve to every visitor). A visually hidden `<h1>` keeps the page
readable for screen readers and search engines, and the date badge is only rendered when
the artwork, which already shows the date, is missing. To change the header, replace the
JPEG; if the file is ever removed the page falls back to the typographic title.

The page also hides the website navigation bar (`no_header`), so only the event itself is
shown.

After upgrading the module: **Events → Halloweentocht → Go to Website** opens the page.
To add the flyer image as cover, use the website editor's cover options on that page.

## Access rights

Two groups under the **Sterrenboom** privilege:

| Group | Members | Events | Implied Odoo Events group |
| --- | --- | --- | --- |
| User | read | read, write, create | Events / User |
| Manager | full | full | Events / Administrator |

## Versioning

The manifest version follows the Odoo convention `19.0.<major>.<minor>.<patch>`. Bump it
in `sterrenboom/__manifest__.py` whenever a change requires a module upgrade, and record
the change in [CHANGELOG.md](CHANGELOG.md).

## License

LGPL-3 — see [LICENSE](LICENSE).

## Author

Data Forge — <https://github.com/DF-DataForge>
