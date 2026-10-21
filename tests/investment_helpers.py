"""Shared helpers for the investments domain tests."""

import uuid
from typing import Any

INVESTMENTS = "/v1/investments"
MARKET_PRICES = "/v1/market-prices"
VALUATIONS = "/v1/valuations"


def create(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"name": "Holding", "investment_type": "stock", **fields}
    return client.post(INVESTMENTS, headers=owner, json=body)


def create_price(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "instrument_key": "SET:TEST",
        "price": 10,
        "as_of": "2026-10-20T10:00:00+00:00",
        "source_type": "exchange",
        **fields,
    }
    return client.post(MARKET_PRICES, headers=owner, json=body)


def create_valuation(
    client: Any, owner: dict[str, str], investment_id: int, **fields: Any
) -> Any:
    body = {
        "investment_id": investment_id,
        "valuation_as_of": "2026-10-20T10:00:00+00:00",
        "valuation_method": "manual",
        **fields,
    }
    return client.post(VALUATIONS, headers=owner, json=body)


def other_workspace(harness: Any, platform: Any) -> dict[str, str]:
    """A token for a second owner in a different workspace."""
    actor = uuid.uuid4()
    platform.grants[actor] = set(harness.cell.permissions())
    return harness.token(actor, uuid.uuid4())
