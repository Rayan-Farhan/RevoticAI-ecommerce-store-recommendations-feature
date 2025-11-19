from pydantic import BaseModel
from typing import Optional

class ShopBase(BaseModel):
    id: int
    name: str
    address: Optional[str] = None

    class Config:
        from_attributes = True

    # The ShopNear schema has been removed to avoid duplication with ShopOut.