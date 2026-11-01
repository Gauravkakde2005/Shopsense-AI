from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    category: Optional[str] = None
    budget: Optional[float] = None
    brand: Optional[str] = None


class ProductOffer(BaseModel):
    offer_id: str
    product_id: str
    retailer_name: str
    retailer_product_url: str
    currency: str = "INR"
    listed_price: Optional[float] = None
    discounted_price: Optional[float] = None
    shipping_cost: Optional[float] = None
    availability: Optional[str] = "Unknown"
    offer_timestamp: Optional[str] = None
    source_type: str = "demo"
    verification_status: str = "demo_data"


class ProductReviewSummary(BaseModel):
    product_id: str
    source_provider: str
    average_rating: Optional[float] = None
    rating_scale: int = 5
    review_count: int = 0
    reviews_analyzed: int = 0
    positive_themes: List[str] = Field(default_factory=list)
    negative_themes: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    review_timestamp: Optional[str] = None


class ProductRecord(BaseModel):
    product_id: str
    canonical_product_name: str
    brand: str
    category: str
    model_number: Optional[str] = None
    description: str
    image_url: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_provider: str = "demo_provider"
    source_product_url: Optional[str] = None
    retrieval_timestamp: Optional[str] = None
    dataset_label: str = "demo"
    rating: Optional[float] = None
    review_count: int = 0
    price_inr: Optional[float] = None
    review_summary: ProductReviewSummary
    offers: List[ProductOffer] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    product_id: str
    product_name: str
    brand: str
    price_inr: Optional[float]
    retailer_name: str
    retailer_url: str
    rating: Optional[float]
    review_count: int
    budget_compliant: bool
    score: float
    preference_match: float
    confidence: float
    explanation: str
    source_label: str
    data_freshness: str


class SearchResponse(BaseModel):
    query: str
    parsed_requirements: Dict[str, Any]
    recommendations: List[RecommendationItem]
    source_status: str


class CompareRequest(BaseModel):
    product_ids: List[str] = Field(..., min_items=2, max_items=5)


class SearchHistoryEntry(BaseModel):
    query: str
    created_at: str


class SavedProductEntry(BaseModel):
    product_id: str
    saved_at: str
