import re
from typing import Any, Dict, List


def parse_search_query(query: str) -> Dict[str, Any]:
    text = (query or "").strip()
    normalized_text = text.replace("₹", " INR ").replace("Rs", " INR ").replace("rs", " INR ")
    lower = normalized_text.lower()
    category = "Watch" if "watch" in lower else "Laptop" if "laptop" in lower else "Headphones" if "headphone" in lower else "General"

    brand_match = re.search(r"\b(titan|noise|fasttrack|boat|sony|apple|asus|dell|lenovo|oneplus)\b", normalized_text, re.IGNORECASE)
    brand = brand_match.group(1).title() if brand_match else None

    budget_match = re.search(r"(?:under|below|within|max|budget|inr)\s*([0-9,]+)", normalized_text, re.IGNORECASE)
    if not budget_match:
        budget_match = re.search(r"(?:inr|rs)\s*([0-9,]+)", normalized_text, re.IGNORECASE)
    max_budget = None if not budget_match else int(budget_match.group(1).replace(",", ""))

    dial_color = None
    for color in ["black", "blue", "silver", "gold", "red", "white"]:
        if color in lower:
            dial_color = color
            break

    return {
        "query": text,
        "brand": brand,
        "category": category,
        "max_budget": max_budget,
        "dial_color": dial_color,
        "weights": {"rating": 0.3, "review": 0.25, "value": 0.25, "preference": 0.2},
    }


def _rating_score(product: Dict[str, Any]) -> float:
    rating = product.get("rating") or 0
    return min(max((rating / 5.0) * 100, 0), 100)


def _review_score(product: Dict[str, Any]) -> float:
    review_summary = product.get("review_summary") or {}
    sentiment = review_summary.get("sentiment_score") or 0
    return min(max(float(sentiment), 0), 100)


def _value_score(product: Dict[str, Any], max_budget: int | None) -> float:
    price = product.get("price_inr")
    if price is None:
        return 50.0
    if max_budget is None:
        return 80.0 if price <= 8000 else 60.0
    if price > max_budget:
        return 0.0
    return max(0.0, 100.0 - (abs(price - max_budget) / max_budget) * 100.0)


def _preference_score(product: Dict[str, Any], requirement: Dict[str, Any]) -> float:
    attributes = product.get("attributes", {})
    required = []
    matched = 0

    if requirement.get("brand"):
        required.append("brand")
        if product.get("brand", "").lower() == requirement["brand"].lower():
            matched += 1

    if requirement.get("category"):
        required.append("category")
        if product.get("category", "").lower() == requirement["category"].lower():
            matched += 1

    if requirement.get("dial_color"):
        required.append("dial_color")
        if (attributes.get("dial_color") or "").lower() == requirement["dial_color"].lower():
            matched += 1

    if not required:
        return 75.0
    return (matched / len(required)) * 100.0


def rank_products(products: List[Dict[str, Any]], requirement: Dict[str, Any]) -> List[Dict[str, Any]]:
    weights = requirement.get("weights", {"rating": 0.3, "review": 0.25, "value": 0.25, "preference": 0.2})
    ranked = []
    for product in products:
        if requirement.get("max_budget") and product.get("price_inr") is not None and product["price_inr"] > requirement["max_budget"]:
            continue
        rating_w = _rating_score(product)
        review_w = _review_score(product)
        value_w = _value_score(product, requirement.get("max_budget"))
        preference_w = _preference_score(product, requirement)
        final = (
            weights.get("rating", 0.3) * rating_w +
            weights.get("review", 0.25) * review_w +
            weights.get("value", 0.25) * value_w +
            weights.get("preference", 0.2) * preference_w
        )
        ranked.append({
            "product_id": product.get("product_id"),
            "product_name": product.get("canonical_product_name"),
            "brand": product.get("brand"),
            "category": product.get("category"),
            "price_inr": product.get("price_inr"),
            "rating": product.get("rating"),
            "review_count": product.get("review_count", 0),
            "score": round(final, 2),
            "budget_compliant": requirement.get("max_budget") is None or (product.get("price_inr") is not None and product["price_inr"] <= requirement["max_budget"]),
            "preference_match": round(preference_w, 2),
            "confidence": round((rating_w * 0.5 + review_w * 0.5) / 100.0 * 100.0, 2),
            "explanation": "Matches the requested budget and preference profile with verified demo pricing.",
            "retailer_name": product.get("retailer_name", "Demo Retailer"),
            "retailer_url": product.get("retailer_url", product.get("source_product_url")),
        })
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked
