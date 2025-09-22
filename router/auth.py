from fastapi import APIRouter, Depends, HTTPException
from models.auth import UserIn, UserOut, LoginRequest, Token, RefreshRequest, UserProfile, PasswordResetRequest
from database import users_collection
from utils.tokens import create_access_token, create_refresh_token, get_current_user
from datetime import datetime
import bcrypt

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(user: UserIn):
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(user.password)
    await users_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "hashed_password": hashed_pw,
        "refresh_token": None,
        "cart": [],
        "wishlist": [],
        "cards": [],
        "history": [],
        "created_at": datetime.utcnow()
    })
    return UserOut(email=user.email)

@router.post("/login", response_model=Token, status_code=200)
async def login(user: LoginRequest):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    await users_collection.update_one(
        {"email": user.email},
        {"$set": {"refresh_token": refresh_token}}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    return UserProfile(
        name=user["name"],
        email=user["email"],
        phone=user.get("phone"),
        created_at=str(user["created_at"])
    )

@router.post("/reset-password", status_code=200)
async def reset_password(data: PasswordResetRequest):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = user.get("otp")
    otp_expiry = user.get("otp_expires")

    if not stored_otp or stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if not otp_expiry or datetime.utcnow() > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    hashed_pw = hash_password(data.new_password)

    await users_collection.update_one(
        {"email": data.email},
        {
            "$set": {"hashed_password": hashed_pw},
            "$unset": {"otp": "", "otp_expires": ""}
        }
    )

    return {"message": "Password reset successful"}
