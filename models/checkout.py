from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Union
from enum import Enum
from models.payment import (
    PaymentMethod,
    CardPaymentData,
    UPIPaymentData,
    NetBankingPaymentData,
    CODPaymentData
)

class AddressType(str, Enum):
    home = "home"
    work = "work"
    other = "other"

class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    phone: str

class ShippingAddress(BaseModel):
    full_name: str
    mobile: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None
    address_type: Optional[AddressType] = AddressType.home

    @validator('pincode')
    def validate_pincode(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('PIN code must be 6 digits')
        return v

    @validator('mobile')
    def validate_mobile(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Mobile number must be 10 digits')
        return v

class CartItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int

class PricingSummary(BaseModel):
    subtotal: float
    delivery_fee: float
    total: float

class CheckoutRequest(BaseModel):
    customer_info: CustomerInfo
    shipping_address: ShippingAddress
    pricing: PricingSummary
    delivery_option: str  # You can replace with Enum if needed
    payment_method: PaymentMethod
    payment_data: Union[
        CardPaymentData,
        UPIPaymentData,
        NetBankingPaymentData,
        CODPaymentData
    ]
