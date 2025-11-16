from pydantic import BaseModel
from typing import Optional, List


class ProductBase(BaseModel):
    id: int
    name: str
    category_id: Optional[int] = None
    shop_id: int

    class Config:
        from_attributes = True


class ProductRecommendation(BaseModel):
    product_id: int
    product_name: str
    shop_id: int
    category_id: Optional[int] = None
    score: float
    reasons: Optional[List[str]] = None
