from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: Optional[str] = None
    preferences: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class PreferencesUpdate(BaseModel):
    preferences: Dict
