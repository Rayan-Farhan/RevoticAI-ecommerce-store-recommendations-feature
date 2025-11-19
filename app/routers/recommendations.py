from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.recommendation_service import (
    get_nearby_shops_service,
    recommend_products_hybrid
)
from app.schemas.recommendation import ShopOut, ProductRecommendationsResponse

router = APIRouter(prefix="/recommend", tags=["recommendations"])

@router.get("/shops", response_model=list[ShopOut])
def get_shops(lat: float, lon: float, radius_km: float = 5.0, db: Session = Depends(get_db)):
    return get_nearby_shops_service(db, lat, lon, radius_km)

@router.get("/products", response_model=ProductRecommendationsResponse)
def get_products(user_id: int, lat: float, lon: float, radius_km: float = 5.0, limit: int = 20, db: Session = Depends(get_db)):
    shops, recs = recommend_products_hybrid(db, user_id, lat, lon, radius_km, limit)
    return ProductRecommendationsResponse(shops=shops, recommended_products=recs)