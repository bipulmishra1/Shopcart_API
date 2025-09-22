from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class SortField(str, Enum):
    price = "price"
    rating = "rating"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class MobileSearchQuery(BaseModel):
    brand: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    color: Optional[str] = Field(None)
    storage: Optional[str] = Field(None)
    memory: Optional[str] = Field(None)
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    sort_by: Optional[SortField] = Field(None)
    order: SortOrder = Field(SortOrder.asc)
    page: int = Field(1, gt=0)
    limit: int = Field(10, gt=0)
