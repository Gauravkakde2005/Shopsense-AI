from __future__ import annotations

from typing import Any, Dict, List

from app.providers.live_provider import search_products


def discover_products(requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = requirements.get("query") or "watch"
    candidates = search_products(query)
    return candidates
