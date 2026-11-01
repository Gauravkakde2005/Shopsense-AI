from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

_history: List[Dict[str, str]] = []
_saved_products: Dict[str, str] = {}


def add_search_history(query: str) -> None:
    _history.append({"query": query, "created_at": datetime.now(timezone.utc).isoformat()})


def get_search_history() -> List[Dict[str, str]]:
    return list(_history)


def save_product(product_id: str) -> str:
    _saved_products[product_id] = datetime.now(timezone.utc).isoformat()
    return product_id


def remove_product(product_id: str) -> None:
    _saved_products.pop(product_id, None)


def get_saved_products() -> Dict[str, str]:
    return dict(_saved_products)
