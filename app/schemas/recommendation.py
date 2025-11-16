from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

from .shop import ShopNear
from .product import ProductRecommendation


class RecommendationRequest(BaseModel):
    user_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(5.0, gt=0, description="Search radius in kilometers")
    limit: int = Field(20, gt=0, le=100)


class RecommendationResponse(BaseModel):
    nearby_shops: List[ShopNear]
    recommendations: List[ProductRecommendation]
