"""What investments refuse: unknown kinds, negative money, bad references between holdings, prices and valuations."""

from investment_helpers import (
    INVESTMENTS,
    MARKET_PRICES,
    VALUATIONS,
    create,
    create_price,
    create_valuation,
    other_workspace,
)

# --- investment ------------------------------------------------------------------------------


def test_investment_name_is_required(client, owner):
    response = client.post(INVESTMENTS, headers=owner, json={"investment_type": "etf"})
    assert response.status_code == 422


def test_investment_name_is_limited_to_200_characters(client, owner):
    assert create(client, owner, name="x" * 201).status_code == 422
    assert create(client, owner, name="y" * 200).status_code == 201


def test_investment_type_is_required(client, owner):
    response = client.post(INVESTMENTS, headers=owner, json={"name": "Untyped"})
    assert response.status_code == 422


def test_investment_type_must_be_a_known_kind(client, owner):
    response = create(client, owner, name="Odd kind", investment_type="nft")
    assert response.status_code == 422


def test_every_listed_investment_type_is_accepted(client, owner):
    kinds = (
        "stock",
        "etf",
        "fund",
        "bond",
        "crypto",
        "real_estate",
        "business",
        "other",
    )
    for kind in kinds:
        response = create(client, owner, name=f"Kind {kind}", investment_type=kind)
        assert response.status_code == 201, (kind, response.text)


def test_investment_status_must_be_a_known_status(client, owner):
    response = create(client, owner, name="Odd status", status="frozen")
    assert response.status_code == 422


def test_owner_scope_must_be_a_known_scope(client, owner):
    response = create(client, owner, name="Odd scope", owner_scope="family")
    assert response.status_code == 422


def test_quantity_and_values_cannot_be_negative(client, owner):
    for field in ("quantity", "cost_basis", "current_value"):
        refused = create(client, owner, name=f"Neg {field}", **{field: -1})
        assert refused.status_code == 422, field
        accepted = create(client, owner, name=f"Zero {field}", **{field: 0})
        assert accepted.status_code == 201, field


def test_instrument_key_is_limited_to_160_characters(client, owner):
    assert (
        create(client, owner, name="Long key", instrument_key="k" * 161).status_code
        == 422
    )
    assert (
        create(client, owner, name="Max key", instrument_key="k" * 160).status_code
        == 201
    )


def test_currency_code_is_at_most_12_characters(client, owner):
    assert create(client, owner, name="Long ccy", currency="C" * 13).status_code == 422
    assert create(client, owner, name="USD holding", currency="USD").status_code == 201


def test_acquired_on_must_be_a_real_calendar_date(client, owner):
    response = create(client, owner, name="Bad date", acquired_on="2026-02-30")
    assert response.status_code == 422


def test_investment_metadata_must_be_an_object(client, owner):
    for bad in (["not", "an", "object"], "text", 5):
        response = create(client, owner, name="Bad meta", metadata=bad)
        assert response.status_code == 422, bad
    assert create(client, owner, name="Good meta", metadata={"a": 1}).status_code == 201


# --- market price ----------------------------------------------------------------------------


def test_a_price_needs_an_instrument_a_price_a_time_and_a_source(client, owner):
    full = {
        "instrument_key": "SET:PTT",
        "price": 33.5,
        "as_of": "2026-10-20T10:00:00+00:00",
        "source_type": "exchange",
    }
    for missing in full:
        body = {k: v for k, v in full.items() if k != missing}
        response = client.post(MARKET_PRICES, headers=owner, json=body)
        assert response.status_code == 422, missing


def test_a_price_cannot_be_negative(client, owner):
    assert create_price(client, owner, price=-0.01).status_code == 422
    assert (
        create_price(client, owner, instrument_key="SET:ZERO", price=0).status_code
        == 201
    )


def test_price_source_type_must_be_a_known_source(client, owner):
    refused = create_price(client, owner, source_type="rumour")
    assert refused.status_code == 422


def test_price_quality_must_be_a_known_quality(client, owner):
    refused = create_price(client, owner, quality="great")
    assert refused.status_code == 422


def test_price_instrument_key_is_limited_to_160_characters(client, owner):
    assert create_price(client, owner, instrument_key="k" * 161).status_code == 422
    assert create_price(client, owner, instrument_key="k" * 160).status_code == 201


def test_price_time_must_be_a_real_timestamp(client, owner):
    assert create_price(client, owner, as_of="yesterday").status_code == 422


# --- valuation -------------------------------------------------------------------------------


def test_a_valuation_needs_an_investment_a_time_and_a_method(client, owner):
    holding = create(client, owner, name="Needs fields").json()
    full = {
        "investment_id": holding["id"],
        "valuation_as_of": "2026-10-20T10:00:00+00:00",
        "valuation_method": "manual",
    }
    for missing in full:
        body = {k: v for k, v in full.items() if k != missing}
        response = client.post(VALUATIONS, headers=owner, json=body)
        assert response.status_code == 422, missing


def test_a_valuation_cannot_point_at_a_missing_investment(client, owner):
    response = create_valuation(client, owner, 987654321)
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {"error": "reference_not_found"}


def test_a_valuation_cannot_point_at_a_missing_market_price(client, owner):
    holding = create(client, owner, name="Priced wrong").json()
    response = create_valuation(client, owner, holding["id"], market_price_id=987654321)
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {"error": "reference_not_found"}


def test_a_valuation_cannot_use_an_investment_of_another_workspace(
    client, owner, harness, platform
):
    holding = create(client, owner, name="Mine").json()
    stranger = other_workspace(harness, platform)
    response = create_valuation(client, stranger, holding["id"])
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {"error": "reference_not_found"}


def test_a_valuation_cannot_use_a_price_of_another_workspace(
    client, owner, harness, platform
):
    stranger = other_workspace(harness, platform)
    theirs = create(client, stranger, name="Theirs").json()
    price = create_price(client, owner, instrument_key="SET:MINE").json()
    response = create_valuation(
        client, stranger, theirs["id"], market_price_id=price["id"]
    )
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == {"error": "reference_not_found"}


def test_a_valuation_cannot_be_moved_to_a_missing_investment(client, owner):
    holding = create(client, owner, name="Stays put").json()
    valuation = create_valuation(client, owner, holding["id"]).json()
    path = f"{VALUATIONS}/{valuation['id']}"
    refused = client.patch(path, headers=owner, json={"investment_id": 987654321})
    assert refused.status_code == 422, refused.text
    assert client.get(path, headers=owner).json()["investment_id"] == holding["id"]


def test_valuation_method_must_be_a_known_method(client, owner):
    holding = create(client, owner, name="Method").json()
    refused = create_valuation(client, owner, holding["id"], valuation_method="guess")
    assert refused.status_code == 422


def test_valuation_coverage_status_must_be_a_known_status(client, owner):
    holding = create(client, owner, name="Coverage").json()
    refused = create_valuation(client, owner, holding["id"], coverage_status="mostly")
    assert refused.status_code == 422


def test_valuation_quantity_and_market_value_cannot_be_negative(client, owner):
    holding = create(client, owner, name="Neg value").json()
    for field in ("quantity", "market_value"):
        refused = create_valuation(client, owner, holding["id"], **{field: -1})
        assert refused.status_code == 422, field
