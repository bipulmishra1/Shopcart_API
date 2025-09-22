from pydantic import BaseModel
from enum import Enum
from typing import Optional

class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    COD = "cod"

class CardPaymentData(BaseModel):
    card_id: Optional[str] = None

class UPIPaymentData(BaseModel):
    upi_id: Optional[str] = None

class NetBankingPaymentData(BaseModel):
    bank_code: str
    bank_name: str

class CODPaymentData(BaseModel):
    confirm: bool = True
