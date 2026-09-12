# VBS De Sterrenboom — Parent Committee

[![CI](https://github.com/DF-DataForge/VBSDeSterrenboom/actions/workflows/ci.yml/badge.svg)](https://github.com/DF-DataForge/VBSDeSterrenboom/actions/workflows/ci.yml)
[![Odoo](https://img.shields.io/badge/Odoo-19.0-875A7B)](https://www.odoo.com/documentation/19.0/)
[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue)](LICENSE)

Odoo 19 addon for managing the parent committee (oudercomité) of VBS De Sterrenboom:
a member register with committee roles, and event planning with attendee tracking,
a status workflow, chatter and scheduled activities.

## Repository layout

This repository **is an Odoo addons path**. The addon lives in a folder named after its
technical name, so the repo can be cloned straight onto a server without renaming anything.

```
VBSDeSterrenboom/            <- add THIS folder to addons_path
├── sterrenboom/             <- the addon (technical name: sterrenboom)
│   ├── __manifest__.py
│   ├── models/
│   │   ├── sterrenboom_member.py
│   │   └── sterrenboom_event.py
│   ├── views/
│   │   ├── sterrenboom_member_views.xml
│   │   ├── sterrenboom_event_views.xml
│   │   └── sterrenboom_menus.xml
│   ├── security/
│   │   ├── sterrenboom_groups.xml
│   │   └── ir.model.access.csv
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

`pre-commit` runs ruff (lint + format) and `pylint-odoo` with Odoo 19 checks enabled:

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

## Access rights

Two groups under the **Sterrenboom** privilege:

| Group | Members | Events |
| --- | --- | --- |
| User | read | read, write, create |
| Manager | full | full |

## Versioning

The manifest version follows the Odoo convention `19.0.<major>.<minor>.<patch>`. Bump it
in `sterrenboom/__manifest__.py` whenever a change requires a module upgrade, and record
the change in [CHANGELOG.md](CHANGELOG.md).

## License

LGPL-3 — see [LICENSE](LICENSE).

## Author

Data Forge — <https://github.com/DF-DataForge>
