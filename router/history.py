from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId
from models.history import EnrichedHistoryItem, FilteredHistoryResponse
from database import users_collection, products_collection
from utils.tokens import get_current_user

router = APIRouter(prefix="/api/v1/history", tags=["History"])



@router.get("/filter", response_model=FilteredHistoryResponse, status_code=200)
async def filter_history(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    user = await users_collection.find_one({"email": current_user["email"]})
    history = user.get("history", [])
    filtered = []

    for entry in reversed(history):
        ts = entry["viewed_at"]
        if start_dt and ts < start_dt:
            continue
        if end_dt and ts > end_dt:
            continue

        product = await products_collection.find_one({"_id": ObjectId(entry["product_id"])})
        if not product:
            continue
        if brand and brand.lower() not in product.get("Brand", "").lower():
            continue
        if model and model.lower() not in product.get("Model", "").lower():
            continue

        filtered.append(EnrichedHistoryItem(
            product_id=str(product["_id"]),
            name=product.get("name", ""),
            brand=product.get("Brand"),
            model=product.get("Model"),
            price=float(product.get("price", 0)),
            viewed_at=ts,
            image_urls=product.get("Product Photo", "").strip().split("\n")
        ))

    return FilteredHistoryResponse(filtered_history=filtered[:20])
