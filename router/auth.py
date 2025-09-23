from fastapi import APIRouter, Depends, HTTPException
from models.auth import UserIn, UserOut, LoginRequest, Token, RefreshRequest, UserProfile, PasswordResetRequest
from database import users_collection
from utils.tokens import (
    create_access_token,
    create_refresh_token,
    get_current_user
)
from datetime import datetime
from jose import jwt, JWTError
import bcrypt

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

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

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "email": db_user["email"],
        "name": db_user.get("name", ""),
        "username": db_user.get("username", db_user["email"].split("@")[0])
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = await users_collection.find_one({"email": email})
    if not user or user.get("refresh_token") != body.refresh_token:
        raise HTTPException(status_code=403, detail="Refresh token has expired or is invalid")
    
    new_access = create_access_token({"sub": email})
    new_refresh = create_refresh_token({"sub": email})

    await users_collection.update_one(
        {"email": email},
        {"$set": {"refresh_token": new_refresh}}
    )

    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
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

@router.get("/protected", status_code=200)
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Access granted for {current_user['email']}"}


@router.post("/logout", status_code=200)
async def logout(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"refresh_token": None}}
    )
    return {"message": "Logged out successfully"}

