from pydantic import BaseModel, EmailStr
from typing import Optional

class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class RemoveItem(BaseModel):
    product_id: str

class Card(BaseModel):
    last4: str
    brand: str
    expiry: str

class CardRemove(BaseModel):
    card_id: str

class HistoryEntry(BaseModel):
    product_id: str

class DefaultCard(BaseModel):
    card_id: str

class UserOut(BaseModel):
    email: EmailStr