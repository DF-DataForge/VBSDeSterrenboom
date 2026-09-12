# Contributing

## Before you push

```bash
pre-commit run --all-files
```

CI will reject anything the hooks would have fixed, so run them locally first.

## Branches and commits

- `main` is deployable at all times; CloudPepper pulls from it.
- Work on `feature/<short-name>` or `fix/<short-name>` and open a pull request.
- Conventional commit subjects, scoped to the addon:
  `[FIX] sterrenboom: prevent duplicate member emails`
  Prefixes: `[ADD]`, `[FIX]`, `[IMP]`, `[REF]`, `[REM]`, `[DOC]`, `[CI]`.

## Odoo 19 conventions used here

These are the ones that most often get written the old way — Odoo 19 changed them:

| Don't | Do |
| --- | --- |
| `<tree>` | `<list>` |
| `view_mode="tree,form"` | `view_mode="list,form"` |
| `<div class="oe_chatter">` | `<chatter/>` |
| `_sql_constraints = [(...)]` | `_name = models.Constraint('unique (col)', "msg")` |
| `res.users` field `groups_id` | `group_ids` |
| `res.groups` field `category_id` → `ir.module.category` | `privilege_id` → `res.groups.privilege` |
| `attrs="{'invisible': [...]}"` | `invisible="state != 'planned'"` |

Other rules:

- One model per file in `models/`, imported in `models/__init__.py`.
- View files are named `<model>_views.xml`; menus live in `sterrenboom_menus.xml`.
- Every new model needs a line per group in `security/ir.model.access.csv`.
- Every new field or behaviour gets a test in `sterrenboom/tests/`.
- Never delete records in code where archiving (`active`) is enough.
- User-facing strings go through `_()`; use `_("x %s", val)`, not `%`-formatting.

## Bumping the version

Any change that adds or alters models, fields, views or data needs a manifest version
bump in `sterrenboom/__manifest__.py` (`19.0.X.Y.Z`) plus a `CHANGELOG.md` entry —
otherwise the server will not pick the change up on upgrade.

## Secrets

Never commit tokens, deploy keys, database dumps or filestore contents. `.gitignore`
blocks the usual suspects and pre-commit's `detect-private-key` hook is a backstop, not
a guarantee.
