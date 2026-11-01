from __future__ import annotations

from typing import Any, Dict, List


def normalize_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "offer_id": offer.get("offer_id") or f"offer_{offer.get('retailer_name', 'demo')}",
        "retailer_name": offer.get("retailer_name", "Demo Retailer"),
        "retailer_product_url": offer.get("retailer_product_url") or "https://example.com/demo-offer",
        "currency": offer.get("currency", "INR"),
        "listed_price": offer.get("listed_price"),
        "discounted_price": offer.get("discounted_price") or offer.get("listed_price"),
        "shipping_cost": offer.get("shipping_cost"),
        "availability": offer.get("availability", "In stock"),
        "offer_timestamp": offer.get("offer_timestamp"),
        "source_type": offer.get("source_type", "demo"),
        "verification_status": offer.get("verification_status", "demo_data"),
    }


def normalize_product(product: Dict[str, Any]) -> Dict[str, Any]:
    offers = [normalize_offer(offer) for offer in product.get("offers", [])]
    offers = sorted(offers, key=lambda offer: offer.get("discounted_price") or float("inf"))
    price = offers[0].get("discounted_price") if offers else product.get("price_inr")
    normalized = dict(product)
    normalized["price_inr"] = price
    normalized["offers"] = offers
    normalized["review_summary"] = product.get("review_summary") or {
        "positive_themes": [],
        "negative_themes": [],
        "sentiment_score": 0,
        "reviews_analyzed": 0,
    }
    normalized["attributes"] = product.get("attributes", {})
    normalized["dataset_label"] = product.get("dataset_label", "demo")
    return normalized


def deduplicate_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for product in products:
        normalized = normalize_product(product)
        key = (
            (normalized.get("brand") or "").lower(),
            (normalized.get("category") or "").lower(),
            (normalized.get("model_number") or normalized.get("canonical_product_name") or "").lower(),
        )
        if key not in grouped:
            grouped[key] = normalized
            continue

        existing = grouped[key]
        existing_offers = existing.get("offers", []) + normalized.get("offers", [])
        seen = {}
        merged_offers = []
        for offer in existing_offers:
            offer_key = offer.get("retailer_name") or offer.get("retailer_product_url")
            if offer_key not in seen:
                seen[offer_key] = offer
                merged_offers.append(offer)
        existing["offers"] = sorted(merged_offers, key=lambda offer: offer.get("discounted_price") or float("inf"))
        existing["price_inr"] = existing["offers"][0].get("discounted_price") if existing["offers"] else existing.get("price_inr")
        if (normalized.get("rating") or 0) > (existing.get("rating") or 0):
            existing["rating"] = normalized.get("rating")
        if (normalized.get("review_count") or 0) > (existing.get("review_count") or 0):
            existing["review_count"] = normalized.get("review_count")

    return list(grouped.values())
