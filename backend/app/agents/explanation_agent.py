from __future__ import annotations

from typing import Any, Dict, List


def explain_recommendations(recommendations: List[Dict[str, Any]], requirements: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    explained = []
    for item in recommendations:
        product_name = item.get("product_name") or "This product"
        explanation = (
            f"{product_name} scored {item.get('score', 0)} with "
            f"{item.get('preference_match', 0)}% preference alignment based on retrieved data."
        )
        enriched = dict(item)
        enriched["explanation"] = explanation
        explained.append(enriched)
    return explained
