from __future__ import annotations

from typing import Any, Dict, List

from app.services.ranking import rank_products


def rank_candidates(products: List[Dict[str, Any]], requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    return rank_products(products, requirements)
