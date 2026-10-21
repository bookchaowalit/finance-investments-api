"""Defaults, uniqueness and imports of investments, market prices and valuations."""

from investment_helpers import (
    INVESTMENTS,
    MARKET_PRICES,
    VALUATIONS,
    create,
    create_price,
    create_valuation,
)

# --- investment ------------------------------------------------------------------------------


def test_new_investment_defaults_to_personal_active_thb(client, owner):
    response = create(client, owner, name="Fresh")
    assert response.status_code == 201, response.text
    holding = response.json()
    assert holding["owner_scope"] == "personal"
    assert holding["status"] == "active"
    assert holding["currency"] == "THB"
    assert holding["version"] == 1
    for field in ("account_id", "quantity", "cost_basis", "current_value", "metadata"):
        assert holding[field] is None, field


def test_investment_values_keep_their_decimal_value(client, owner):
    holding = create(
        client,
        owner,
        name="Decimals",
        quantity=12.5,
        cost_basis=1000.25,
        current_value=1234.56,
    ).json()
    assert holding["quantity"] == 12.5
    assert holding["cost_basis"] == 1000.25
    assert holding["current_value"] == 1234.56


def test_two_investments_may_share_a_name_and_instrument(client, owner):
    first = create(client, owner, name="Twin", instrument_key="SET:TWIN")
    second = create(client, owner, name="Twin", instrument_key="SET:TWIN")
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text


def test_account_id_is_a_plain_number_not_a_checked_reference(client, owner):
    holding = create(client, owner, name="Held in", account_id=424242)
    assert holding.status_code == 201, holding.text
    assert holding.json()["account_id"] == 424242


def test_investment_import_keeps_the_old_id(client, owner):
    imported = create(client, owner, name="Imported", legacy_id=1818)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 1818
    found = client.get(f"{INVESTMENTS}/legacy/1818", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["name"] == "Imported"
    assert create(client, owner, name="Again", legacy_id=1818).status_code == 409


# --- market price ----------------------------------------------------------------------------


def test_new_price_defaults_to_provisional_thb(client, owner):
    response = create_price(client, owner, instrument_key="SET:DEFAULTS")
    assert response.status_code == 201, response.text
    price = response.json()
    assert price["quality"] == "provisional"
    assert price["currency"] == "THB"
    assert price["version"] == 1
    assert price["source_ref"] is None


def test_a_price_is_unique_per_instrument_time_and_source(client, owner):
    base = {"instrument_key": "SET:UNIQ", "as_of": "2026-10-20T10:00:00+00:00"}
    assert create_price(client, owner, **base).status_code == 201
    assert create_price(client, owner, price=11, **base).status_code == 409


def test_the_same_price_time_is_allowed_for_another_source_or_instrument(client, owner):
    base = {"instrument_key": "SET:MULTI", "as_of": "2026-10-20T10:00:00+00:00"}
    assert create_price(client, owner, **base).status_code == 201
    other_source = create_price(client, owner, source_type="broker", **base)
    other_instrument = create_price(
        client, owner, instrument_key="SET:OTHER", as_of=base["as_of"]
    )
    other_time = create_price(
        client, owner, instrument_key="SET:MULTI", as_of="2026-10-21T10:00:00+00:00"
    )
    assert other_source.status_code == 201, other_source.text
    assert other_instrument.status_code == 201, other_instrument.text
    assert other_time.status_code == 201, other_time.text


def test_price_import_keeps_the_old_id(client, owner):
    imported = create_price(client, owner, instrument_key="SET:IMP", legacy_id=909)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 909
    found = client.get(f"{MARKET_PRICES}/legacy/909", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["instrument_key"] == "SET:IMP"


# --- valuation -------------------------------------------------------------------------------


def test_new_valuation_defaults_to_unpriced_thb(client, owner):
    holding = create(client, owner, name="Valued").json()
    response = create_valuation(client, owner, holding["id"])
    assert response.status_code == 201, response.text
    valuation = response.json()
    assert valuation["coverage_status"] == "unpriced"
    assert valuation["currency"] == "THB"
    assert valuation["market_price_id"] is None
    assert valuation["version"] == 1


def test_a_valuation_may_cite_a_market_price(client, owner):
    holding = create(client, owner, name="Priced").json()
    price = create_price(client, owner, instrument_key="SET:CITED").json()
    valuation = create_valuation(
        client,
        owner,
        holding["id"],
        market_price_id=price["id"],
        valuation_method="market_price",
        quantity=10,
        market_value=100.5,
        coverage_status="covered",
    )
    assert valuation.status_code == 201, valuation.text
    assert valuation.json()["market_price_id"] == price["id"]
    assert valuation.json()["market_value"] == 100.5


def test_an_investment_has_one_valuation_per_moment(client, owner):
    holding = create(client, owner, name="Once").json()
    assert create_valuation(client, owner, holding["id"]).status_code == 201
    again = create_valuation(client, owner, holding["id"], market_value=5)
    assert again.status_code == 409


def test_the_same_valuation_moment_is_allowed_for_another_investment_or_time(
    client, owner
):
    first = create(client, owner, name="First").json()
    second = create(client, owner, name="Second").json()
    assert create_valuation(client, owner, first["id"]).status_code == 201
    other_holding = create_valuation(client, owner, second["id"])
    other_time = create_valuation(
        client, owner, first["id"], valuation_as_of="2026-10-21T10:00:00+00:00"
    )
    assert other_holding.status_code == 201, other_holding.text
    assert other_time.status_code == 201, other_time.text


def test_moving_a_valuation_onto_a_taken_moment_is_refused(client, owner):
    holding = create(client, owner, name="Collide").json()
    create_valuation(client, owner, holding["id"])
    later = create_valuation(
        client, owner, holding["id"], valuation_as_of="2026-10-21T10:00:00+00:00"
    ).json()
    clash = client.patch(
        f"{VALUATIONS}/{later['id']}",
        headers=owner,
        json={"valuation_as_of": "2026-10-20T10:00:00+00:00"},
    )
    assert clash.status_code == 409


def test_valuation_import_keeps_the_old_id(client, owner):
    holding = create(client, owner, name="Import host").json()
    imported = create_valuation(client, owner, holding["id"], legacy_id=616)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 616
    found = client.get(f"{VALUATIONS}/legacy/616", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["investment_id"] == holding["id"]
