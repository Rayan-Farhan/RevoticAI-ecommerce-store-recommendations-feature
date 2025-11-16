from pydantic import BaseModel
from typing import Optional


class ShopBase(BaseModel):
    id: int
    name: str
    address: Optional[str] = None

    class Config:
        from_attributes = True


class ShopNear(ShopBase):
    distance_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
