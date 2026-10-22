# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/finance-investments-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, and the only tests were the generic contract suite; the rules of investments, market prices and valuations (kinds, non-negative money, uniqueness, references, delete protection) were not tested.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — An investment needs a name and a known type, and money cannot be negative

- **Given** an owner with write permission
- **When** they create an investment without a name or type, with type `nft`, or with a negative `quantity`, `cost_basis` or `current_value`
- **Then** the API answers 422 for each; every listed type is accepted and 0 is accepted for the amounts
- **Test:** `tests/test_investment_validation.py::test_investment_type_must_be_a_known_kind` · level: integration (API + throwaway PostgreSQL)

### AC-02 — A price needs instrument, price, time and source, and cannot be negative

- **Given** an owner with write permission
- **When** they create a market price missing one of those four fields, or with a negative price or an unknown source or quality
- **Then** the API answers 422 for each; a price of 0 is accepted
- **Test:** `tests/test_investment_validation.py::test_a_price_needs_an_instrument_a_price_a_time_and_a_source` · level: integration (API + throwaway PostgreSQL)

### AC-03 — A price is unique per instrument, moment and source

- **Given** a price for `SET:UNIQ` at 2026-10-20T10:00Z from an exchange
- **When** another with the same instrument, moment and source is created, then one with another source, instrument or moment
- **Then** the first repeat is refused with 409 and the others are created
- **Test:** `tests/test_investment_defaults.py::test_a_price_is_unique_per_instrument_time_and_source` · level: integration (API + throwaway PostgreSQL)

### AC-04 — A valuation must point at records of the same workspace

- **Given** an investment and a market price
- **When** a valuation is created for a missing investment, a missing price, or an investment or price of another workspace
- **Then** the API answers 422 `reference_not_found`
- **Test:** `tests/test_investment_validation.py::test_a_valuation_cannot_use_an_investment_of_another_workspace` · level: integration (API + throwaway PostgreSQL)

### AC-05 — An investment has one valuation per moment

- **Given** an investment valued at 2026-10-20T10:00Z
- **When** another valuation for the same moment is created, or one is moved onto it
- **Then** the API answers 409; the same moment for another investment, or another moment, is accepted
- **Test:** `tests/test_investment_defaults.py::test_an_investment_has_one_valuation_per_moment` · level: integration (API + throwaway PostgreSQL)

### AC-06 — Records that are still referenced cannot be deleted

- **Given** an investment with a valuation, and a price cited by a valuation
- **When** the owner deletes the investment or the price, then the valuation, then the investment or price again
- **Then** the first delete answers 409 `has_dependents`; after the valuation is gone the delete succeeds
- **Test:** `tests/test_investment_queries.py::test_an_investment_with_valuations_cannot_be_deleted` · level: integration (API + throwaway PostgreSQL)

### AC-07 — New records take their documented defaults

- **Given** create requests with only the required fields
- **When** an investment, a price and a valuation are created
- **Then** the investment is personal, active and THB; the price is provisional and THB; the valuation is unpriced and THB; each has version 1
- **Test:** `tests/test_investment_defaults.py::test_new_investment_defaults_to_personal_active_thb` · level: integration (API + throwaway PostgreSQL)

### AC-08 — Prices and valuations are listed by time and filtered

- **Given** prices and valuations created out of time order
- **When** the owner lists by `instrument_key` or `investment_id`, ascending and descending
- **Then** only matching records come back, oldest first (newest first with `order=desc`); stats refuse fields that are not filters
- **Test:** `tests/test_investment_queries.py::test_prices_are_listed_by_time_not_by_creation` · level: integration (API + throwaway PostgreSQL)

### AC-09 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `/v1/*` (all resources) | unchanged | same routes and payloads; see README |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "56"` (measured 58.61% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_investment_validation.py::test_investment_type_must_be_a_known_kind` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-02 | `tests/test_investment_validation.py::test_a_price_needs_an_instrument_a_price_a_time_and_a_source` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-03 | `tests/test_investment_defaults.py::test_a_price_is_unique_per_instrument_time_and_source` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_investment_validation.py::test_a_valuation_cannot_use_an_investment_of_another_workspace` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_investment_defaults.py::test_an_investment_has_one_valuation_per_moment` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_investment_queries.py::test_an_investment_with_valuations_cannot_be_deleted` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_investment_defaults.py::test_new_investment_defaults_to_personal_active_thb` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_investment_queries.py::test_prices_are_listed_by_time_not_by_creation` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-09 | `tests/test_contract.py::test_numbers_fit_their_columns` | 0548c5a · `.venv/bin/pytest -q -k numbers_fit` · `ValueError: Out of range float values are not JSON compliant: nan` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
