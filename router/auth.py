from fastapi import APIRouter, Depends, HTTPException
from models.schemas import UserIn, UserOut, LoginRequest, Token, RefreshRequest
from database import users_collection
from utils.tokens import create_access_token, create_refresh_token, get_current_user
from jose import JWTError, jwt
from config import ACCESS_SECRET_KEY, REFRESH_SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta
import bcrypt

router = APIRouter(tags=["Auth"])

# Hash password using bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verify password using bcrypt
def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# Create refresh token with expiry
def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    data.update({"exp": expire})
    return jwt.encode(data, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

# ✅ Signup route
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
        "history": []
    })
    return UserOut(email=user.email)

# ✅ Login route with username and email
@router.post("/login")
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
        "user": {
            "email": db_user["email"],
            "name": db_user.get("name", ""),
            "username": db_user.get("username", db_user["email"].split("@")[0])
        }
    }

# ✅ Refresh token route
@router.post("/refresh", response_model=Token)
async def refresh_token(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
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
    
    return Token(access_token=new_access, token_type="bearer")

# ✅ Protected route for testing token
@router.get("/protected")
async def protected(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Welcome, {current_user['email']}! You are authenticated ✅"
    }

# ✅ Logout route
@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"refresh_token": None}}
    )
    return {"message": "Logged out successfully"}
