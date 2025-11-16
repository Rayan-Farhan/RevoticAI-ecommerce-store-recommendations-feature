from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.schemas.shop import ShopNear
from app.schemas.product import ProductRecommendation
from app.services.recommendation_service import recommend_products

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)):
    if payload.radius_km <= 0:
        raise HTTPException(status_code=400, detail="radius_km must be > 0")

    shops_out, recs_out = recommend_products(
        db=db,
        user_id=payload.user_id,
        lat=payload.latitude,
        lon=payload.longitude,
        radius_km=payload.radius_km,
        limit=payload.limit,
    )

    return RecommendationResponse(
        nearby_shops=[ShopNear(**s) for s in shops_out],
        recommendations=[ProductRecommendation(**r) for r in recs_out],
    )
