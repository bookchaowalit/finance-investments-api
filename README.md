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
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/investments-db provision
npm install && railway config apply && railway up --ci --service investments-api
railway scale --service investments-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Railway variables: `INVESTMENTS_DB_MODE=hosted`, `INVESTMENTS_DB_URL_API`,
`INVESTMENTS_JWT_PUBLIC_KEY_PEM`, `INVESTMENTS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
