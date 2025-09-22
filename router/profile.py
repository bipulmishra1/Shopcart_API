from fastapi import APIRouter, Depends, HTTPException
from models.profile import UserProfile, ProfileUpdate
from database import users_collection
from utils.tokens import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])

# ✅ View current user profile
@router.get("/", response_model=UserProfile, status_code=200)
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(
        name=user["name"],
        email=user["email"],
        phone=user["phone"],
        address=user.get("address"),
        preferences=user.get("preferences"),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at")
    )

# ✅ Update name or email
@router.put("/update", status_code=200)
async def update_profile(update: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    updates = {}
    if update.name:
        updates["name"] = update.name
    if update.email:
        existing = await users_collection.find_one({"email": update.email})
        if existing and existing["email"] != current_user["email"]:
            raise HTTPException(status_code=400, detail="Email already in use")
        updates["email"] = update.email

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    updates["updated_at"] = datetime.utcnow()

    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": updates}
    )

    return {"message": "Profile updated successfully"}
