import json
from pathlib import Path
from typing import Any, Dict, List


DATA_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "data" / "demo_products.json",
    Path(__file__).resolve().parents[2] / "data" / "demo_products.json",
]

DATA_PATH = next((path for path in DATA_CANDIDATES if path.exists()), DATA_CANDIDATES[0])


def _normalize_product(item: Dict[str, Any]) -> Dict[str, Any]:
    offers = item.get("offers", []) or []
    best_offer = min(
        offers,
        key=lambda offer: (offer.get("discounted_price") or offer.get("listed_price") or float("inf")),
        default={},
    )
    price = best_offer.get("discounted_price") or best_offer.get("listed_price")
    normalized = dict(item)
    normalized["price_inr"] = price
    normalized["retailer_name"] = best_offer.get("retailer_name", "Demo Retailer")
    normalized["retailer_url"] = best_offer.get("retailer_product_url", item.get("source_product_url"))
    normalized["rating"] = item.get("rating")
    normalized["review_count"] = item.get("review_count", 0)
    return normalized


def get_mock_products() -> List[Dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return [_normalize_product(item) for item in json.load(handle)]


def search_products(query: str) -> List[Dict[str, Any]]:
    products = get_mock_products()
    query_lower = query.lower()
    filtered = []
    for product in products:
        if query_lower:
            haystack = " ".join([
                product.get("brand", ""),
                product.get("category", ""),
                product.get("canonical_product_name", ""),
                product.get("model_number", ""),
                *product.get("attributes", {}).values(),
            ]).lower()
            if any(token in haystack for token in [
                "watch",
                "titan",
                "noise",
                "fasttrack",
                "black",
                "blue",
                "daily",
                "style",
            ]):
                filtered.append(product)
    return filtered or products
