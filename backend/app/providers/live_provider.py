from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from app.config import AI_REQUEST_TIMEOUT_SECONDS, SERPAPI_KEY, SERPAPI_LOCATION


class ProviderConfigurationError(RuntimeError):
    """Raised when live retrieval cannot run without a provider credential."""


class ProviderRequestError(RuntimeError):
    """Raised when the authorized provider fails or returns invalid data."""


def _number(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"[0-9][0-9,]*(?:\.[0-9]+)?", str(value))
    return float(match.group(0).replace(",", "")) if match else None


def _integer(value: Any) -> int:
    number = _number(value)
    return int(number) if number is not None else 0


def _product_id(link: str, title: str) -> str:
    digest = hashlib.sha256(f"{link}|{title}".encode("utf-8")).hexdigest()[:16]
    return f"web_{digest}"


def _normalize_result(item: Dict[str, Any]) -> Dict[str, Any] | None:
    title = (item.get("title") or "").strip()
    link = (item.get("link") or item.get("product_link") or "").strip()
    if not title or not link:
        return None

    price = _number(item.get("price"))
    retailer = (item.get("source") or item.get("merchant") or "Unknown source").strip()
    rating = _number(item.get("rating"))
    review_count = _integer(item.get("reviews"))
    now = datetime.now(timezone.utc).isoformat()
    return {
        "product_id": _product_id(link, title),
        "canonical_product_name": title,
        "brand": item.get("brand") or title.split(" ")[0],
        "category": "General",
        "model_number": None,
        "description": item.get("snippet") or "Retrieved product listing; details are provided by the source.",
        "image_url": item.get("thumbnail"),
        "attributes": {},
        "source_provider": "serpapi_google_shopping",
        "source_product_url": link,
        "retrieval_timestamp": now,
        "dataset_label": "live_web",
        "rating": rating,
        "review_count": review_count,
        "price_inr": price,
        "review_summary": {
            "positive_themes": [],
            "negative_themes": [],
            "sentiment_score": None,
            "reviews_analyzed": 0,
        },
        "offers": [{
            "offer_id": f"offer_{_product_id(link, title)}",
            "retailer_name": retailer,
            "retailer_product_url": link,
            "currency": "INR",
            "listed_price": None,
            "discounted_price": price,
            "shipping_cost": None,
            "availability": item.get("availability") or "Unknown",
            "offer_timestamp": now,
            "source_type": "authorized_search_provider",
            "verification_status": "retrieved",
        }],
    }


def search_products(query: str) -> List[Dict[str, Any]]:
    if not SERPAPI_KEY:
        raise ProviderConfigurationError(
            "Live product search is not configured. Set SERPAPI_KEY in backend/.env."
        )

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "location": SERPAPI_LOCATION,
        "hl": "en",
        "gl": "in",
    }
    try:
        response = httpx.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=AI_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ProviderRequestError(f"Live product search failed: {exc}") from exc

    if payload.get("error"):
        raise ProviderRequestError(str(payload["error"]))

    products = [_normalize_result(item) for item in payload.get("shopping_results", [])]
    return [product for product in products if product is not None]