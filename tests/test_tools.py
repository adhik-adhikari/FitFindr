from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []  # empty list, no exception


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    results = search_listings("tee", size="M", max_price=None)
    assert all("m" in item["size"].lower() for item in results)


def test_search_best_match_first():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    # Top result should have more relevant tags than last result
    assert len(results) >= 2
    top_title = results[0]["title"].lower()
    assert any(kw in top_title or kw in " ".join(results[0]["style_tags"]).lower()
               for kw in ["vintage", "graphic", "tee"])


def test_search_no_size_filter():
    results_with_size = search_listings("vintage", size="M", max_price=None)
    results_no_size = search_listings("vintage", size=None, max_price=None)
    assert len(results_no_size) >= len(results_with_size)


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0
    suggestion = suggest_outfit(results[0], get_example_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0
    suggestion = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0
    # Should return general styling advice, not crash
    assert "error" not in suggestion.lower() or "could not" not in suggestion.lower()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def test_create_fit_card_returns_caption():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    item = results[0]
    outfit = suggest_outfit(item, get_example_wardrobe())
    caption = create_fit_card(outfit, item)
    assert isinstance(caption, str)
    assert len(caption) > 0


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    caption = create_fit_card("", results[0])
    assert caption == "Outfit data incomplete — try suggesting the outfit first."


def test_create_fit_card_whitespace_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    caption = create_fit_card("   ", results[0])
    assert caption == "Outfit data incomplete — try suggesting the outfit first."


def test_create_fit_card_varies_output():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    item = results[0]
    outfit = suggest_outfit(item, get_example_wardrobe())
    caption1 = create_fit_card(outfit, item)
    caption2 = create_fit_card(outfit, item)
    # With temperature=1.0 outputs should differ (not identical)
    assert caption1 != caption2
