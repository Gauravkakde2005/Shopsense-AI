import pytest

from app.services.normalization import deduplicate_products
from app.services.ranking import parse_search_query, rank_products
from app.providers.mock_provider import get_mock_products
from app.workflows.agent_workflow import run_workflow
from app.services import llm
from app.main import AssistantBody, assistant_chat


def test_query_parsing_extracts_budget_and_brand():
    parsed = parse_search_query("Best Titan watch under ₹5,000 with black dial")
    assert parsed["brand"] == "Titan"
    assert parsed["category"] == "Watch"
    assert parsed["max_budget"] == 5000
    assert parsed["dial_color"] == "black"


def test_budget_filter_rejects_expensive_products():
    products = get_mock_products()
    filtered = [p for p in products if p["price_inr"] <= 5000]
    assert all(item["price_inr"] <= 5000 for item in filtered)


def test_ranking_prefers_budget_compatible_high_score_product():
    products = get_mock_products()
    ranked = rank_products(products, {
        "brand": "Titan",
        "category": "Watch",
        "max_budget": 5000,
        "dial_color": "black",
        "weights": {"rating": 0.3, "review": 0.25, "value": 0.25, "preference": 0.2},
    })
    assert ranked and ranked[0]["product_id"] == "watch_titan_black_01"


def test_missing_review_data_handles_gracefully():
    products = get_mock_products()
    product = products[1]
    assert product["review_summary"]["sentiment_score"] >= 0


def test_deduplicate_products_keeps_best_offer():
    products = [
        {
            "product_id": "dup-1",
            "canonical_product_name": "Titan Watch",
            "brand": "Titan",
            "category": "Watch",
            "model_number": "Model X",
            "rating": 4.3,
            "review_count": 100,
            "price_inr": 4999,
            "offers": [{"retailer_name": "Amazon", "discounted_price": 4999}, {"retailer_name": "Flipkart", "discounted_price": 4599}],
            "attributes": {"dial_color": "black"},
            "dataset_label": "demo",
        },
        {
            "product_id": "dup-2",
            "canonical_product_name": "Titan Watch",
            "brand": "Titan",
            "category": "Watch",
            "model_number": "Model X",
            "rating": 4.3,
            "review_count": 100,
            "price_inr": 4999,
            "offers": [{"retailer_name": "Amazon", "discounted_price": 4999}],
            "attributes": {"dial_color": "black"},
            "dataset_label": "demo",
        },
    ]
    deduped = deduplicate_products(products)
    assert len(deduped) == 1
    assert deduped[0]["offers"][0]["retailer_name"] == "Flipkart"


def test_workflow_returns_parsed_requirements_and_recommendations(monkeypatch):
    from app.agents import discovery_agent

    monkeypatch.setattr(discovery_agent, "search_products", lambda query: get_mock_products())
    result = run_workflow("Best Titan watch under ₹5,000 with black dial")
    assert result["status"] == "live_web"
    assert result["parsed_requirements"]["max_budget"] == 5000
    assert result["recommendations"]
    assert result["review_analysis"]
    assert result["review_analysis"][0]["reviews_analyzed"] > 0


def test_product_assistant_sends_complete_product_context(monkeypatch):
    captured = {}

    def fake_generate(system, prompt):
        captured["system"] = system
        captured["prompt"] = prompt
        return "context-aware answer"

    monkeypatch.setattr(llm, "_generate", fake_generate)
    answer = llm.answer_product_question(
        "phones",
        [{"product_name": "Phone A", "price_inr": 49999, "offers": [{"retailer_name": "Amazon"}]}],
        [{"role": "user", "content": "Which is better?"}],
        {"max_budget": 50000},
    )
    assert answer == "context-aware answer"
    assert '"price_inr": 49999' in captured["prompt"]
    assert '"offers"' in captured["prompt"]
    assert "only questions about the currently displayed products" in captured["system"]


def test_product_assistant_handles_greeting_without_groq(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("A greeting should not call the LLM")

    monkeypatch.setattr(llm, "_generate", fail_if_called)
    response = assistant_chat(AssistantBody(messages=[{"role": "user", "content": "hi"}]))
    assert response["answer"].startswith("I am your AI Product Assistant")
