from pathlib import Path

import pytest

from pricing import (
    calculate_basket,
    filter_by_category,
    load_products,
    parse_items,
    price_per_base,
)


@pytest.fixture
def products():
    """Small fake price table, so tests don't depend on real prices."""
    return [
        {"name": "chicken breast", "category": "protein", "pack_size": 500.0, "unit": "g", "price_eur": 4.00},
        {"name": "eggs", "category": "protein", "pack_size": 10.0, "unit": "piece", "price_eur": 2.00},
        {"name": "spaghetti", "category": "carb", "pack_size": 500.0, "unit": "g", "price_eur": 1.00},
    ]


def test_price_per_100g(products):
    assert price_per_base(products[0]) == pytest.approx(0.80)


def test_price_per_piece(products):
    assert price_per_base(products[1]) == pytest.approx(0.20)


def test_filter_by_category(products):
    result = filter_by_category(products, "protein")
    assert [p["name"] for p in result] == ["chicken breast", "eggs"]


def test_filter_without_category_returns_everything(products):
    assert len(filter_by_category(products)) == 3


def test_parse_items_basic():
    result = parse_items("chicken breast:700:g; eggs:6:piece")
    assert result == [
        {"name": "chicken breast", "amount": 700.0, "unit": "g"},
        {"name": "eggs", "amount": 6.0, "unit": "piece"},
    ]


def test_parse_items_rejects_missing_unit():
    with pytest.raises(ValueError):
        parse_items("chicken breast:700")


def test_parse_items_rejects_non_numeric_amount():
    with pytest.raises(ValueError):
        parse_items("eggs:six:piece")


def test_basket_rounds_up_to_whole_packs(products):
    result = calculate_basket(products, parse_items("chicken breast:700:g"))
    assert result["lines"][0]["packs"] == 2
    assert result["total_eur"] == 8.00


def test_basket_adds_up_same_product_before_rounding(products):
    result = calculate_basket(products, parse_items("chicken breast:200:g;chicken breast:200:g"))
    assert result["lines"][0]["packs"] == 1
    assert result["total_eur"] == 4.00


def test_basket_total_across_products(products):
    result = calculate_basket(
        products, parse_items("chicken breast:700:g;eggs:6:piece;spaghetti:400:g")
    )
    assert result["total_eur"] == 11.00


def test_basket_reports_unmatched_items(products):
    result = calculate_basket(products, parse_items("caviar:100:g;eggs:100:g"))
    assert len(result["unmatched"]) == 2
    assert result["total_eur"] == 0.0


def test_real_price_file_is_valid():
    path = Path(__file__).parent.parent / "data" / "prices.csv"
    products = load_products(path)
    assert len(products) > 0
    for p in products:
        assert p["pack_size"] > 0
        assert p["price_eur"] > 0
        assert p["unit"] in {"g", "ml", "piece"}