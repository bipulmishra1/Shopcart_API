from pydantic import BaseModel, EmailStr
from typing import Optional

class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str

class UserOut(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class RefreshRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    phone: str
    created_at: Optional[str]

class PasswordResetRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
