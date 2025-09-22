from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class HistoryEntry(BaseModel):
    product_id: str

class HistoryRecord(BaseModel):
    product_id: str
    viewed_at: datetime



class EnrichedHistoryItem(BaseModel):
    product_id: str
    name: str
    brand: Optional[str]
    model: Optional[str]
    price: Optional[float]
    viewed_at: datetime
    image_urls: Optional[List[str]] = []



class FilteredHistoryResponse(BaseModel):
    filtered_history: List[EnrichedHistoryItem]
