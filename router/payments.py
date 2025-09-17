from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from uuid import uuid4
from models.schemas import CheckoutRequest, OrderResponse
from database import users_collection
from utils.tokens import get_current_user

router = APIRouter()

@router.post("/checkout", response_model=OrderResponse)
async def checkout(data: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    cart = user.get("cart", [])
    cards = user.get("cards", [])

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    card = next((c for c in cards if c["card_id"] == data.payment_card_id), None)
    if not card:
        raise HTTPException(status_code=400, detail="Invalid payment card")

    # Simulate payment
    transaction_id = str(uuid4())

    # Simulate shipping
    tracking_id = str(uuid4())
    estimated_delivery = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d")

    # Create order
    order = {
        "email": user["email"],
        "items": cart,
        "payment": {
            "card_id": data.payment_card_id,
            "last4": card["last4"],
            "brand": card["brand"],
            "transaction_id": transaction_id
        },
        "shipping": {
            "address": data.shipping_address,
            "tracking_id": tracking_id,
            "estimated_delivery": estimated_delivery
        },
        "timestamp": datetime.utcnow(),
        "status": "confirmed"
    }

    result = await users_collection.database["orders"].insert_one(order)

    # Clear cart
    await users_collection.update_one(
        {"email": user["email"]},
        {"$set": {"cart": []}}
    )

    return {
        "order_id": str(result.inserted_id),
        "transaction_id": transaction_id,
        "tracking_id": tracking_id,
        "estimated_delivery": estimated_delivery,
        "message": "Checkout complete! Order confirmed."
    }
