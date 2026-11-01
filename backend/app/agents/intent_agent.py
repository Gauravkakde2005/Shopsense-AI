import re
from typing import Any, Dict

from app.services.llm import enhance_intent


def understand_intent(query: str) -> Dict[str, Any]:
    text = (query or "").strip()
    normalized_text = text.replace("₹", " INR ").replace("Rs", " INR ").replace("rs", " INR ")
    lower = normalized_text.lower()
    category = "Watch" if "watch" in lower else "Laptop" if "laptop" in lower else "Headphones" if "headphone" in lower else "General"

    brand_match = re.search(r"\b(titan|noise|fasttrack|boat|sony|apple|asus|dell|lenovo|oneplus)\b", normalized_text, re.IGNORECASE)
    brand = brand_match.group(1).title() if brand_match else None
    budget_match = re.search(r"(?:under|below|within|max|budget|inr)\s*([0-9,]+)", normalized_text, re.IGNORECASE)
    if not budget_match:
        budget_match = re.search(r"(?:inr|rs)\s*([0-9,]+)", normalized_text, re.IGNORECASE)
    max_budget = int(budget_match.group(1).replace(",", "")) if budget_match else None

    dial_color = None
    for color in ["black", "blue", "silver", "gold", "red", "white"]:
        if color in lower:
            dial_color = color
            break

    baseline = {
        "query": text,
        "brand": brand,
        "category": category,
        "max_budget": max_budget,
        "dial_color": dial_color,
        "weights": {"rating": 0.3, "review": 0.25, "value": 0.25, "preference": 0.2},
    }
    return enhance_intent(text, baseline)
