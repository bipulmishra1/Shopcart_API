from pydantic import BaseModel, HttpUrl
from typing import Optional

class WishlistItem(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: HttpUrl

class RemoveItem(BaseModel):
    product_id: str

class CartItem(BaseModel):
    product_id: str
    quantity: int
