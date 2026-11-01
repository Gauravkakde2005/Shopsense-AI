from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from app.config import AI_REQUEST_TIMEOUT_SECONDS, GEMINI_API_BASE_URL, GEMINI_API_KEY, GEMINI_MODEL


def _generate(system: str, user: str, json_mode: bool = False) -> str | None:
    if not GEMINI_API_KEY:
        return None
    try:
        response = httpx.post(
            f"{GEMINI_API_BASE_URL}/models/{GEMINI_MODEL}:generateContent",
            params={"key": GEMINI_API_KEY},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "temperature": 0,
                    **({"responseMimeType": "application/json"} if json_mode else {}),
                },
            },
            timeout=AI_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None


def enhance_intent(query: str, baseline: Dict[str, Any]) -> Dict[str, Any]:
    prompt = (
        "Extract shopping requirements from this request. Return JSON only with keys "
        "category, brand, max_budget, dial_color, and keywords. Preserve null when unknown. "
        f"Request: {query}"
    )
    raw = _generate("You extract structured shopping intent. Never invent constraints.", prompt, json_mode=True)
    if not raw:
        return baseline
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return baseline
    merged = dict(baseline)
    for key in ("category", "brand", "dial_color"):
        if isinstance(parsed.get(key), str) and parsed[key].strip():
            merged[key] = parsed[key].strip()
    budget = parsed.get("max_budget")
    if isinstance(budget, (int, float)) and budget > 0:
        merged["max_budget"] = int(budget)
    elif isinstance(budget, str):
        try:
            parsed_budget = int(float(budget.replace(",", "").strip()))
            if parsed_budget > 0:
                merged["max_budget"] = parsed_budget
        except ValueError:
            pass
    if isinstance(parsed.get("keywords"), list):
        merged["keywords"] = [item for item in parsed["keywords"] if isinstance(item, str)][:12]
    return merged


def explain_with_llm(item: Dict[str, Any], requirements: Dict[str, Any]) -> str | None:
    facts = {
        "name": item.get("product_name"),
        "brand": item.get("brand"),
        "price": item.get("price_inr"),
        "rating": item.get("rating"),
        "review_count": item.get("review_count"),
        "score": item.get("score"),
        "preference_match": item.get("preference_match"),
        "source": item.get("retailer_name"),
        "requirements": requirements,
    }
    return _generate(
        "Explain shopping recommendations using only supplied facts. Do not invent reviews, prices, availability, or features. Be concise.",
        json.dumps(facts),
    )