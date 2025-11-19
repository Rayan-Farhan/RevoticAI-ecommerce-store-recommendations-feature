from pydantic import BaseModel
from typing import Optional, List

class ShopOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    distance_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProductOut(BaseModel):
    product_id: int
    product_name: str
    shop_id: int
    category_id: Optional[int] = None
    score: float
    cf_score: float
    reasons: Optional[List[str]] = None

class ProductRecommendationsResponse(BaseModel):
    shops: List[ShopOut]
    recommended_products: List[ProductOut]