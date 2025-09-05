from fastapi import APIRouter, Depends, HTTPException
from models.schemas import UserIn, UserOut, LoginRequest, Token, RefreshRequest
from utils.security import hash_password, verify_password
from utils.tokens import create_access_token, create_refresh_token
from database import users_collection
from jose import JWTError, jwt
from config import ACCESS_SECRET_KEY, REFRESH_SECRET_KEY, ALGORITHM
from utils.tokens import get_current_user

router = APIRouter()

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
        "token_type": "bearer"
    }

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

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"refresh_token": None}}
    )
    return {"message": "Logged out successfully"}
