from fastapi import APIRouter, Depends
from database import orders_collection
from utils.tokens import get_current_user

router = APIRouter()

@router.get("/recent")
async def get_recent_orders(current_user: dict = Depends(get_current_user)):
    cursor = orders_collection.find({"email": current_user["email"]}).sort("timestamp", -1).limit(5)
    recent_orders = []
    async for order in cursor:
        order["_id"] = str(order["_id"])
        recent_orders.append(order)
    return {"recent_orders": recent_orders}
