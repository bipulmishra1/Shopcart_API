from pydantic import BaseModel
from typing import Optional

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CartProduct(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int
    image_urls: Optional[list[str]] = []

class CartResponse(BaseModel):
    cart: list[CartProduct]

class CartTotals(BaseModel):
    subtotal: float
    delivery_fee: float
    total: float

class CartResponse(BaseModel):
    cart: list[CartProduct]
    totals: Optional[CartTotals] = None
