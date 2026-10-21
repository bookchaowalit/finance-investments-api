"""Listing, grouping and the lifecycle of investments, market prices and valuations."""

from investment_helpers import (
    INVESTMENTS,
    MARKET_PRICES,
    VALUATIONS,
    create,
    create_price,
    create_valuation,
)

# --- investment ------------------------------------------------------------------------------


def test_list_investments_filters_by_type(client, owner):
    create(client, owner, name="Index", investment_type="etf")
    create(client, owner, name="Coin", investment_type="crypto")
    listed = client.get(
        INVESTMENTS, headers=owner, params={"investment_type": "crypto"}
    )
    assert listed.status_code == 200, listed.text
    assert {item["investment_type"] for item in listed.json()["items"]} == {"crypto"}


def test_list_investments_filters_by_status_and_scope(client, owner):
    create(client, owner, name="Sold stock", status="sold", owner_scope="venture")
    create(client, owner, name="Held stock", owner_scope="venture")
    listed = client.get(
        INVESTMENTS, headers=owner, params={"status": "sold", "owner_scope": "venture"}
    )
    assert listed.status_code == 200, listed.text
    assert [item["name"] for item in listed.json()["items"]] == ["Sold stock"]


def test_list_investments_filters_by_account(client, owner):
    create(client, owner, name="In account 7", account_id=7001)
    create(client, owner, name="In account 8", account_id=7002)
    listed = client.get(INVESTMENTS, headers=owner, params={"account_id": 7001})
    assert listed.status_code == 200, listed.text
    assert [item["name"] for item in listed.json()["items"]] == ["In account 7"]


def test_list_investments_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(INVESTMENTS, headers=owner, params={"instrument_key": "x"})
    assert listed.status_code == 422


def test_investment_stats_count_per_type_and_status(client, owner):
    create(client, owner, name="Bond A", investment_type="bond")
    create(client, owner, name="Bond B", investment_type="bond", status="closed")
    by_type = client.get(
        f"{INVESTMENTS}/stats", headers=owner, params={"group_by": "investment_type"}
    )
    assert by_type.status_code == 200, by_type.text
    assert by_type.json()["groups"]["bond"] >= 2
    by_status = client.get(
        f"{INVESTMENTS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert by_status.json()["groups"]["closed"] >= 1


def test_investment_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{INVESTMENTS}/stats", headers=owner, params={"group_by": "name"}
    )
    assert stats.status_code == 422


def test_selling_an_investment_keeps_its_cost_basis(client, owner):
    holding = create(client, owner, name="To sell", cost_basis=500).json()
    sold = client.patch(
        f"{INVESTMENTS}/{holding['id']}",
        headers=owner,
        json={"status": "sold", "current_value": 0},
    )
    assert sold.status_code == 200, sold.text
    assert sold.json()["status"] == "sold"
    assert sold.json()["cost_basis"] == 500
    assert sold.json()["version"] == 2


def test_an_investment_patch_that_changes_nothing_keeps_the_version(client, owner):
    holding = create(client, owner, name="Stable", metadata={"a": 1}, quantity=3).json()
    same = client.patch(
        f"{INVESTMENTS}/{holding['id']}",
        headers=owner,
        json={"name": "Stable", "metadata": {"a": 1}, "quantity": 3},
    )
    assert same.status_code == 200, same.text
    assert same.json()["version"] == 1


def test_a_negative_value_is_refused_on_investment_update(client, owner):
    holding = create(client, owner, name="Keep value", current_value=900).json()
    path = f"{INVESTMENTS}/{holding['id']}"
    refused = client.patch(path, headers=owner, json={"current_value": -1})
    assert refused.status_code == 422
    assert client.get(path, headers=owner).json()["current_value"] == 900


def test_an_investment_with_valuations_cannot_be_deleted(client, owner):
    holding = create(client, owner, name="Valued").json()
    valuation = create_valuation(client, owner, holding["id"]).json()
    refused = client.delete(f"{INVESTMENTS}/{holding['id']}", headers=owner)
    assert refused.status_code == 409, refused.text
    assert refused.json()["detail"] == {"error": "has_dependents"}
    assert (
        client.delete(f"{VALUATIONS}/{valuation['id']}", headers=owner).status_code
        == 204
    )
    assert (
        client.delete(f"{INVESTMENTS}/{holding['id']}", headers=owner).status_code
        == 204
    )


# --- market price ----------------------------------------------------------------------------


def test_list_prices_filters_by_instrument_and_quality(client, owner):
    create_price(client, owner, instrument_key="SET:AAA", quality="verified")
    create_price(client, owner, instrument_key="SET:AAA", source_type="broker")
    create_price(client, owner, instrument_key="SET:BBB", quality="verified")
    by_instrument = client.get(
        MARKET_PRICES, headers=owner, params={"instrument_key": "SET:AAA"}
    )
    assert {p["instrument_key"] for p in by_instrument.json()["items"]} == {"SET:AAA"}
    verified = client.get(
        MARKET_PRICES,
        headers=owner,
        params={"instrument_key": "SET:AAA", "quality": "verified"},
    )
    assert len(verified.json()["items"]) == 1
    assert verified.json()["items"][0]["quality"] == "verified"


def test_prices_are_listed_by_time_not_by_creation(client, owner):
    for day in ("2026-10-03", "2026-10-01", "2026-10-02"):
        create_price(
            client, owner, instrument_key="SET:ORDER", as_of=f"{day}T09:00:00+00:00"
        )
    params = {"instrument_key": "SET:ORDER"}
    listed = client.get(MARKET_PRICES, headers=owner, params=params).json()["items"]
    days = [p["as_of"][:10] for p in listed]
    assert days == ["2026-10-01", "2026-10-02", "2026-10-03"]
    newest = client.get(
        MARKET_PRICES, headers=owner, params={**params, "order": "desc"}
    )
    assert newest.json()["items"][0]["as_of"].startswith("2026-10-03")


def test_price_stats_count_per_quality(client, owner):
    create_price(client, owner, instrument_key="SET:Q1", quality="stale")
    stats = client.get(
        f"{MARKET_PRICES}/stats", headers=owner, params={"group_by": "quality"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["stale"] >= 1


def test_price_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{MARKET_PRICES}/stats", headers=owner, params={"group_by": "price"}
    )
    assert stats.status_code == 422


def test_rejecting_a_price_bumps_its_version(client, owner):
    price = create_price(client, owner, instrument_key="SET:REJ").json()
    path = f"{MARKET_PRICES}/{price['id']}"
    rejected = client.patch(path, headers=owner, json={"quality": "rejected"})
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["version"] == 2
    same = client.patch(path, headers=owner, json={"quality": "rejected"})
    assert same.json()["version"] == 2


def test_a_price_cited_by_a_valuation_cannot_be_deleted(client, owner):
    holding = create(client, owner, name="Cites price").json()
    price = create_price(client, owner, instrument_key="SET:CITE").json()
    valuation = create_valuation(
        client, owner, holding["id"], market_price_id=price["id"]
    ).json()
    refused = client.delete(f"{MARKET_PRICES}/{price['id']}", headers=owner)
    assert refused.status_code == 409, refused.text
    assert refused.json()["detail"] == {"error": "has_dependents"}
    assert (
        client.delete(f"{VALUATIONS}/{valuation['id']}", headers=owner).status_code
        == 204
    )
    assert (
        client.delete(f"{MARKET_PRICES}/{price['id']}", headers=owner).status_code
        == 204
    )


def test_deleting_an_unused_price_removes_it(client, owner):
    price = create_price(client, owner, instrument_key="SET:GONE").json()
    path = f"{MARKET_PRICES}/{price['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


# --- valuation -------------------------------------------------------------------------------


def test_list_valuations_filters_by_investment_and_coverage(client, owner):
    one = create(client, owner, name="One").json()
    two = create(client, owner, name="Two").json()
    create_valuation(client, owner, one["id"], coverage_status="covered")
    create_valuation(
        client, owner, one["id"], valuation_as_of="2026-10-21T10:00:00+00:00"
    )
    create_valuation(client, owner, two["id"])
    mine = client.get(VALUATIONS, headers=owner, params={"investment_id": one["id"]})
    assert len(mine.json()["items"]) == 2
    covered = client.get(
        VALUATIONS,
        headers=owner,
        params={"investment_id": one["id"], "coverage_status": "covered"},
    )
    assert len(covered.json()["items"]) == 1


def test_valuations_are_listed_by_moment_not_by_creation(client, owner):
    holding = create(client, owner, name="Timeline").json()
    for day in ("2026-10-03", "2026-10-01", "2026-10-02"):
        create_valuation(
            client, owner, holding["id"], valuation_as_of=f"{day}T09:00:00+00:00"
        )
    params = {"investment_id": holding["id"]}
    listed = client.get(VALUATIONS, headers=owner, params=params).json()["items"]
    days = [v["valuation_as_of"][:10] for v in listed]
    assert days == ["2026-10-01", "2026-10-02", "2026-10-03"]


def test_list_valuations_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(VALUATIONS, headers=owner, params={"market_price_id": "1"})
    assert listed.status_code == 422


def test_valuation_stats_count_per_coverage_status(client, owner):
    holding = create(client, owner, name="Stats").json()
    create_valuation(client, owner, holding["id"], coverage_status="stale")
    stats = client.get(
        f"{VALUATIONS}/stats", headers=owner, params={"group_by": "coverage_status"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["stale"] >= 1


def test_valuation_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{VALUATIONS}/stats", headers=owner, params={"group_by": "valuation_method"}
    )
    assert stats.status_code == 422


def test_pricing_a_valuation_later_bumps_its_version(client, owner):
    holding = create(client, owner, name="Priced later").json()
    price = create_price(client, owner, instrument_key="SET:LATER").json()
    valuation = create_valuation(client, owner, holding["id"]).json()
    priced = client.patch(
        f"{VALUATIONS}/{valuation['id']}",
        headers=owner,
        json={
            "market_price_id": price["id"],
            "valuation_method": "market_price",
            "coverage_status": "covered",
            "market_value": 250,
        },
    )
    assert priced.status_code == 200, priced.text
    assert priced.json()["market_price_id"] == price["id"]
    assert priced.json()["version"] == 2


def test_deleting_a_valuation_keeps_its_investment_and_price(client, owner):
    holding = create(client, owner, name="Survivor").json()
    price = create_price(client, owner, instrument_key="SET:SURV").json()
    valuation = create_valuation(
        client, owner, holding["id"], market_price_id=price["id"]
    ).json()
    assert (
        client.delete(f"{VALUATIONS}/{valuation['id']}", headers=owner).status_code
        == 204
    )
    assert (
        client.get(f"{VALUATIONS}/{valuation['id']}", headers=owner).status_code == 404
    )
    assert (
        client.get(f"{INVESTMENTS}/{holding['id']}", headers=owner).status_code == 200
    )
    assert (
        client.get(f"{MARKET_PRICES}/{price['id']}", headers=owner).status_code == 200
    )
