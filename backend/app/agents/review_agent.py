from __future__ import annotations

from typing import Any, Dict, List


def analyze_reviews(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    analyzed = []
    for product in products:
        review = product.get("review_summary") or {}
        sentiment = review.get("sentiment_score") or 0
        positive = review.get("positive_themes") or []
        negative = review.get("negative_themes") or []
        analyzed.append({
            "product_id": product.get("product_id"),
            "positive_themes": positive,
            "negative_themes": negative,
            "sentiment_score": float(sentiment),
            "reviews_analyzed": review.get("reviews_analyzed") or product.get("review_count", 0),
        })
    return analyzed
