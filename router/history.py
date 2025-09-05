from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional
from bson import ObjectId
from models.schemas import HistoryEntry
from database import users_collection, products_collection
from utils.tokens import get_current_user

router = APIRouter()

@router.post("/log")
async def log_history(entry: HistoryEntry, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$push": {"history": {
            "product_id": entry.product_id,
            "timestamp": datetime.utcnow()
        }}}
    )
    return {"message": "Product view logged"}

@router.get("/")
async def get_history(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    history = user.get("history", [])[-20:]
    enriched = []
    for entry in reversed(history):
        product = await products_collection.find_one({"_id": ObjectId(entry["product_id"])})
        if product:
            product["_id"] = str(product["_id"])
            product["viewed_at"] = entry["timestamp"]
            enriched.append(product)
    return {"history": enriched}

@router.get("/filter")
async def filter_history(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    user = await users_collection.find_one({"email": current_user["email"]})
    history = user.get("history", [])
    filtered = []

    for entry in reversed(history):
        ts = entry["timestamp"]
        if start_date and ts < datetime.fromisoformat(start_date):
            continue
        if end_date and ts > datetime.fromisoformat(end_date):
            continue

        product = await products_collection.find_one({"_id": ObjectId(entry["product_id"])})
        if not product:
            continue
        if brand and brand.lower() not in product.get("Brand", "").lower():
            continue
        if model and model.lower() not in product.get("Model", "").lower():
            continue

        product["_id"] = str(product["_id"])
        product["viewed_at"] = ts
        filtered.append(product)

    return {"filtered_history": filtered}

