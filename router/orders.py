from fastapi import APIRouter, Depends
from database import orders_collection
from utils.tokens import get_current_user
from models.order import CheckoutResponse  # ✅ updated import
from datetime import datetime

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

@router.get("/recent", response_model=list[CheckoutResponse], status_code=200)
async def get_recent_orders(current_user: dict = Depends(get_current_user)):
    cursor = orders_collection.find({"email": current_user["email"]}).sort("created_at", -1).limit(5)
    recent_orders = []
    async for order in cursor:
        order["_id"] = str(order["_id"])  # optional: remove if not needed in response
        recent_orders.append(CheckoutResponse(**order))  # ✅ parse into model
    return recent_orders
