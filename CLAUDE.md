# CLAUDE.md

## What this repo is

A single Odoo **19.0** addon, `sterrenboom`, for the parent committee of VBS De
Sterrenboom. The repository root is an Odoo *addons path*: the addon lives in
`sterrenboom/`, and CloudPepper adds the repo root to `addons_path`. Do not move the
addon back to the repo root — Odoo derives the technical name from the folder name.

## Environment notes

- Windows host, PowerShell. `git` is **not on PATH**; it ships with GitHub Desktop at
  `C:\Users\piet_\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd\git.exe`.
- No local Python, pip, Docker or Node. Linters and tests therefore cannot run locally
  right now — CI is the gate. Do not claim tests passed without CI output.
- `git push` cannot be done from an agent shell: the remote is HTTPS and no credential
  helper is configured for `github.com` (GitHub Desktop keeps its token in its own
  store). Commit locally, then push from GitHub Desktop or an interactive terminal.

## Odoo 19 API specifics (verified against the 19.0 source)

Odoo 19 renamed a lot. When writing or reviewing code here:

- List views: root tag `<list>`, and `view_mode="list,form"`.
- Chatter: `<chatter/>` directly after `</sheet>`, not `<div class="oe_chatter">`.
- SQL constraints: class attributes, not `_sql_constraints`:
  `_unique_email = models.Constraint('unique (email)', "message")`
- `res.users` groups field is `group_ids` (was `groups_id`). The rename cascades to
  `ir.actions.*`, `ir.ui.view` and `ir.ui.menu`.
- `res.groups.category_id` → `privilege_id`, pointing at the new `res.groups.privilege`
  model rather than `ir.module.category`. `implied_ids` is unchanged.
- `ir.rule` still uses the `groups` field.
- `groups=` and `web_icon=` attributes on `<menuitem>` are unchanged.
- No `attrs=` / `states=`: use direct expressions, e.g. `invisible="state != 'planned'"`.
- Search views: the group-by container is a bare `<group>`; `expand=` and `string=` on it
  fail RNG validation ("Invalid attribute expand for element group").
- Give every field a distinct label per model, otherwise Odoo logs a "same label" warning.
- Translations: `_("text %s", value)`, never `%`-interpolation inside `_()`.

Check `https://raw.githubusercontent.com/odoo/odoo/19.0/...` when unsure; the rendered
docs site is JS-heavy and WebFetch only returns its nav.

## Conventions

- One model per file in `models/`, imported in `models/__init__.py`.
- `views/<model>_views.xml` per model; all `<menuitem>`s in `views/sterrenboom_menus.xml`.
- Do not import `tests` from `__init__.py` — Odoo discovers the package itself.
- Every model gets a row per group in `security/ir.model.access.csv`.
- Bump `19.0.X.Y.Z` in the manifest and add a `CHANGELOG.md` entry for anything that
  needs a module upgrade on the server.
- Prefer archiving (`active`) over unlinking.
- Records in `<data noupdate="1">` (mail templates, event data) are not touched by an
  upgrade. To ship a text change, add a `migrations/<version>/post-migrate.py` that
  reloads the file with `convert_file(env, 'sterrenboom', 'data/x.xml', None, mode='init')`.

## Commits

`[ADD]|[FIX]|[IMP]|[REF]|[REM]|[DOC]|[CI] sterrenboom: imperative summary`
