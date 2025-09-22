from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.checkout import PricingSummary, CartItem, CustomerInfo, ShippingAddress

class CheckoutResponse(BaseModel):
    success: bool
    order_id: str
    message: str
    payment_id: Optional[str] = None
    payment_url: Optional[str] = None
    qr_code_url: Optional[str] = None
    tracking_id: Optional[str] = None
    estimated_delivery: Optional[str] = None
    status: str
    payment_instructions: Optional[str] = None
    payment_status: str
    created_at: datetime
    updated_at: datetime

class OrderSummary(BaseModel):
    order_id: str
    status: str
    total: float
    created_at: datetime
    updated_at: datetime

class OrderDetailResponse(BaseModel):
    order_id: str
    items: List[CartItem]
    customer_info: CustomerInfo
    shipping_address: ShippingAddress
    pricing: PricingSummary
    status: str
    tracking_id: Optional[str]
    estimated_delivery: Optional[str]
    payment_status: str
    created_at: datetime
    updated_at: datetime
