# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through `life-dashboard-web` (finance page: active investments, with
  current value and cost basis summed per currency), the cell's own MCP server
  (`investments-mcp`) and the hosted tool hub (`platform-mcp-remote-worker`).
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `investments.investment:read|write|delete`, `investments.market-price:read|write|delete` and
  `investments.valuation:read|write|delete`. [ต้องยืนยัน: which job or person writes
  `market-price` and `valuation` rows.]
- `finance-ledger-core` (`book-finance-api`): its boundary doc
  `docs/gates/BOO-140-finance-api-boundary.md` maps `/api/finance/v1/valuations` and
  `/risk-readiness` to this service's `/v1/valuations` and `/v1/market-prices`
  [ต้องยืนยัน: whether that mapping is live].

## Product Purpose

The list of holdings and how they are valued: what the owner holds (stock, etf, fund, bond, crypto,
real_estate, business, other) per owner scope, the market prices seen for an instrument at a moment
with their source and quality, and dated valuations of a holding that may cite one of those prices.
`account_id` can name the account in `finance-accounts-api` that holds the investment.

Success: every holding exists once with its cost basis and current value, and a valuation records
how its value was reached (market price, cost basis, manual or unpriced) and how well it is covered.

## Positioning

One capability, one service: its own API (Railway), its own database (Neon) with row-level
security per workspace, and authorization, executions and audit through `empire-platform`. It is
workspace-scoped, so the same service can serve other tenants without code changes.

## Operating Context

- Production: `https://investments-api-production.up.railway.app` (`/health`), deployed by merging
  to `main` after CI.
- Data starts empty (created 2026-10-12 from the retired `finance_*` tables' fields); imports keep
  old ids in `legacy_id`.
- Monitored by `platform-uptime-worker` (probed hourly, because the service sleeps when idle);
  errors go to Sentry without personal data.

## Capabilities and Constraints

- `/v1/investments`: list (filters `investment_type`, `owner_scope`, `status`, `account_id`;
  ordered by id), stats (grouped by one of those filters), get, get-by-legacy-id, create (with
  `Idempotency-Key`), patch (with `expected_version`), delete.
- `/v1/market-prices`: the same routes; filters `instrument_key`, `quality`; listed by `as_of`
  (then id).
- `/v1/valuations`: the same routes; filters `investment_id`, `coverage_status`; listed by
  `valuation_as_of` (then id).
- Investment rules: `name` (at most 200 characters) and `investment_type` are required; `status` is
  planned, active (default), sold or closed; `owner_scope` defaults to personal; `quantity`,
  `cost_basis` and `current_value` cannot be negative; `instrument_key` is at most 160 characters;
  `currency` defaults to THB; `metadata` is a JSON object. Names are not unique. `account_id` is a
  plain number, not a foreign key.
- Market-price rules: `instrument_key`, `price` (not negative), `as_of` and `source_type`
  (exchange, broker, custodian, manual, derived) are required; `quality` (verified, provisional,
  stale, rejected) defaults to provisional; one price per instrument, moment and source type (409).
- Valuation rules: `investment_id`, `valuation_as_of` and `valuation_method` (market_price,
  cost_basis, manual, unpriced) are required; `investment_id` and the optional `market_price_id`
  must exist in the same workspace (otherwise 422 `reference_not_found`); `coverage_status`
  (covered, partial, unpriced, stale, invalid) defaults to unpriced; `quantity` and `market_value`
  cannot be negative; one valuation per investment and moment (409).
- An investment that has valuations, or a market price that a valuation cites, cannot be deleted
  (409 `has_dependents`); delete the valuations first.
- Not checked: that a valuation's price is for the same instrument as its investment, and that
  `current_value` on the investment agrees with its latest valuation.
- Out of scope: fetching prices from markets, profit and loss, and tax lots.

## Measures

Proposed (nothing collects them yet):

- Active investments whose latest valuation is covered, as a share of all active investments.
- Total current value and cost basis of active investments, per currency (the dashboard already
  shows both).
- 5xx rate and p95 latency on `/v1/investments` (Sentry and uptime worker).
