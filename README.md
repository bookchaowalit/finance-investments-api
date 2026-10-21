# finance-investments-api
The Investments cell: its own API (Railway, serverless) and its own Neon
database, first generated from `cell.yaml` (one of the ten finance
services split on 2026-10-12). It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `finance-investments-api`, service `investments-api` (Serverless) |
| Data | Neon project `finance-investments-api`, database `investments` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`investments`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `investments.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/investments` | investment | `investment_type`, `owner_scope`, `status`, `account_id` |
| `/v1/market-prices` | market-price | `instrument_key`, `quality` |
| `/v1/valuations` | valuation | `investment_id`, `coverage_status` |

## Develop and operate

```bash
uv sync --frozen --all-extras          # Python 3.12 (.python-version): pgserver has no cp313 wheel yet
.venv/bin/pytest -q
.venv/bin/mypy . && uvx ruff@0.17.1 check . && uvx ruff@0.17.1 format --check .   # the same checks CI runs
NEON_API_KEY=... .venv/bin/investments-db provision
npm install && railway config apply   # service settings only; code deploys from GitHub (below)
railway scale --service investments-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Dependencies are locked in `uv.lock`; the image installs them with `uv sync --frozen`, so
production runs the versions CI tested. Change a dependency with `uv add`/`uv lock` and commit
the lock. Product scope and measures: [PRODUCT.md](PRODUCT.md); change records: `specs/`.

Deploys (CD, since 2026-10-18): `investments-api` is connected to this repository's `main` with
Railway's Wait for CI (`checkSuites`). A merge to `main` deploys only after the CI and security
checks pass; a failing check leaves production on the previous deployment. Roll back by
redeploying an earlier deployment in Railway. `railway up` is no longer used.

Railway variables: `SENTRY_DSN` (error reporting; unset = off, see `src/cellkit/_sentry.py`),
`INVESTMENTS_DB_MODE=hosted`, `INVESTMENTS_DB_URL_API`,
`INVESTMENTS_JWT_PUBLIC_KEY_PEM`, `INVESTMENTS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
