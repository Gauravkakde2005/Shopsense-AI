from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import provider_status
from app.providers.live_provider import ProviderConfigurationError, ProviderRequestError
from app.services.ranking import rank_products
from app.services.store import add_search_history, get_saved_products, get_search_history, remove_product, save_product
from app.workflows.agent_workflow import run_workflow

app = FastAPI(title="ShopSense AI API", version="0.1.0")
_live_product_cache: Dict[str, Dict[str, Any]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchBody(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "shopsense-ai",
        "providers": [provider_status()],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/providers")
def providers() -> List[Dict[str, Any]]:
    status = provider_status()
    return [{"name": "serpapi_google_shopping", "mode": "authorized_api", "status": status["product_search_status"], "label": "live_web"}]


@app.post("/api/search")
def search(body: SearchBody) -> Dict[str, Any]:
    try:
        workflow = run_workflow(body.query)
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _live_product_cache.clear()
    _live_product_cache.update({product["product_id"]: product for product in workflow["products"]})
    add_search_history(body.query)
    review_by_id = {item["product_id"]: item for item in workflow.get("review_analysis", [])}
    recommendations = []
    for item in workflow["recommendations"]:
        product = next((p for p in workflow["products"] if p["product_id"] == item["product_id"]), None)
        if not product:
            continue
        review = review_by_id.get(item["product_id"], {})
        recommendations.append({
            "product_id": item["product_id"],
            "product_name": product["canonical_product_name"],
            "brand": product["brand"],
            "price_inr": product["price_inr"],
            "retailer_name": product.get("retailer_name", "Unknown source"),
            "retailer_url": product.get("retailer_url", product.get("source_product_url")),
            "description": product.get("description"),
            "image_url": product.get("image_url"),
            "offers": product.get("offers", []),
            "rating": product.get("rating"),
            "review_count": product.get("review_count", 0),
            "budget_compliant": item["budget_compliant"],
            "score": item["score"],
            "preference_match": item["preference_match"],
            "confidence": item["confidence"],
            "explanation": item["explanation"],
            "source_label": product.get("dataset_label", "live_web"),
            "data_freshness": product.get("retrieval_timestamp", "retrieved"),
            "attributes": product.get("attributes", {}),
            "review_insights": {
                "sentiment_score": review.get("sentiment_score"),
                "reviews_analyzed": review.get("reviews_analyzed", product.get("review_count", 0)),
                "positive_themes": review.get("positive_themes", []),
                "negative_themes": review.get("negative_themes", []),
            },
        })
    return {
        "query": body.query,
        "parsed_requirements": workflow["parsed_requirements"],
        "recommendations": recommendations,
        "source_status": workflow["status"],
    }


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> Dict[str, Any]:
    product = _live_product_cache.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product is not in the current live search session.")
    return product


@app.post("/api/compare")
def compare(body: dict) -> Dict[str, Any]:
    selected_ids = body.get("product_ids", [])
    if not 2 <= len(selected_ids) <= 5:
        raise HTTPException(status_code=400, detail="Select between 2 and 5 products to compare.")
    selected = [_live_product_cache[product_id] for product_id in selected_ids if product_id in _live_product_cache]
    if len(selected) < 2:
        raise HTTPException(status_code=409, detail="Search again before comparing these products.")
    ranked = rank_products(selected, {"max_budget": 100000, "weights": {"rating": 0.3, "review": 0.25, "value": 0.25, "preference": 0.2}})
    return {"product_ids": [product["product_id"] for product in selected], "comparison": ranked, "explanation": "Comparison generated from the latest live provider response."}


@app.post("/api/recommendations/rerank")
def rerank(body: dict) -> Dict[str, Any]:
    product_ids = body.get("product_ids", [])
    weights = body.get("weights", {"rating": 0.3, "review": 0.25, "value": 0.25, "preference": 0.2})
    products = [_live_product_cache[product_id] for product_id in product_ids if product_id in _live_product_cache]
    if not products:
        raise HTTPException(status_code=409, detail="Search again before reranking these products.")
    requirement = {"weights": weights, "max_budget": body.get("max_budget") or 100000}
    return {"ranked_products": rank_products(products, requirement)}


@app.get("/api/search-history")
def search_history() -> List[Dict[str, str]]:
    return get_search_history()


@app.post("/api/saved-products")
def save_product_api(body: dict) -> Dict[str, str]:
    product_id = body.get("product_id")
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    save_product(product_id)
    return {"status": "saved", "product_id": product_id}


@app.delete("/api/saved-products/{product_id}")
def delete_saved_product(product_id: str) -> Dict[str, str]:
    remove_product(product_id)
    return {"status": "deleted", "product_id": product_id}


@app.get("/api/saved-products")
def saved_products() -> Dict[str, str]:
    return get_saved_products()
