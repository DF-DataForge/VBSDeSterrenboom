## What changed

<!-- One or two sentences. -->

## Why

<!-- Link an issue if there is one. -->

## Checklist

- [ ] `pre-commit run --all-files` passes
- [ ] Manifest version bumped in `sterrenboom/__manifest__.py` (if this needs an upgrade)
- [ ] `CHANGELOG.md` updated
- [ ] New/changed models have `security/ir.model.access.csv` entries
- [ ] New/changed behaviour has tests
- [ ] Tested against Odoo 19.0 (locally via `docker compose up -d`, or CI is green)

## Deployment notes

<!-- Anything the CloudPepper deploy needs beyond "pull + restart + upgrade"? -->
