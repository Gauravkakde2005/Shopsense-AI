from __future__ import annotations

from typing import Any, Dict, List


def verify_recommendations(recommendations: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid_ids = {product.get("product_id") for product in products}
    verified = []
    for item in recommendations:
        product_id = item.get("product_id")
        if product_id in valid_ids:
            verified.append(item)
    return verified
