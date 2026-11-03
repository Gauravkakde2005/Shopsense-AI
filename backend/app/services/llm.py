from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from app.config import AI_REQUEST_TIMEOUT_SECONDS, GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL

_last_generation_error = ""


def generation_error() -> str:
    return _last_generation_error


def answer_product_question(
    searched_product: str,
    products: list[Dict[str, Any]],
    messages: list[Dict[str, str]],
    parsed_requirements: Dict[str, Any] | None = None,
    comparison: list[Dict[str, Any]] | None = None,
) -> str | None:
    global _last_generation_error
    _last_generation_error = ""
    context = {
        "searchedProduct": searched_product,
        "products": products,
        "parsedRequirements": parsed_requirements or {},
        "comparison": comparison or [],
    }
    conversation = messages[-20:]
    prompt = (
        "PRODUCT_CONTEXT (the complete current page context):\n"
        f"{json.dumps(context, ensure_ascii=False)}\n\n"
        "CONVERSATION_HISTORY:\n"
        f"{json.dumps(conversation, ensure_ascii=False)}\n\n"
        "Answer the latest user message from the conversation history."
    )
    system = (
        "You are an AI Product Assistant inside a product comparison application. "
        "Use only PRODUCT_CONTEXT as the source of product facts. Never invent prices, "
        "ratings, reviews, sellers, availability, delivery, specifications, links, or products. "
        "You may compare, summarize, explain specifications, discuss value, describe pros and cons, "
        "and recommend alternatives only from the provided products. If a fact is missing, say it is "
        "not available in the current results. Answer only questions about the currently displayed "
        "products. For unrelated questions, reply exactly: "
        "I am your AI Product Assistant. I can only answer questions related to the products currently "
        "displayed. Please ask about the searched products. Keep answers professional, concise, and "
        "well formatted with short headings and bullet points when useful."
    )
    return _generate(system, prompt)


def _generate(system: str, user: str, json_mode: bool = False) -> str | None:
    global _last_generation_error
    if not GROQ_API_KEY:
        _last_generation_error = "Groq is not configured. Set GROQ_API_KEY in backend/.env."
        return None
    try:
        response = httpx.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **({"response_format": {"type": "json_object"}} if json_mode else {}),
            },
            timeout=AI_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            _last_generation_error = "Groq rate or usage limits were reached. Check your Groq plan and try again later."
        elif exc.response.status_code == 503:
            _last_generation_error = "The selected Groq model is temporarily unavailable. Try again later."
        elif exc.response.status_code in (401, 403):
            _last_generation_error = "Groq rejected the API key. Check GROQ_API_KEY in backend/.env."
        elif exc.response.status_code == 413:
            _last_generation_error = "The current product context is larger than your Groq plan allows. Narrow the search results or upgrade the Groq usage tier so the assistant can receive all product details."
        else:
            _last_generation_error = f"Groq returned HTTP {exc.response.status_code}."
        return None
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        _last_generation_error = "Groq could not process the request."
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