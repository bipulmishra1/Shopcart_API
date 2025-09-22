from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
import uuid
import logging

from models.order import CheckoutResponse
from models.checkout import CheckoutRequest, CardPaymentRequest
from database import users_collection, orders_collection
from services.payment_service import PaymentService
from services.order_service import OrderService
from utils.tokens import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/checkout", tags=["Checkout"])

@router.post("/", response_model=CheckoutResponse, status_code=200)
async def place_order(
    checkout_data: CheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Checkout request for user {current_user['email']}: {checkout_data.model_dump()}")

        user = await users_collection.find_one({"email": current_user["email"]})
        cart = user.get("cart", [])
        if not cart:
            raise HTTPException(status_code=400, detail="Cart is empty")

        delivery_days = {"standard": 7, "express": 3, "same-day": 1}
        delivery_option = checkout_data.delivery_option
        if delivery_option not in delivery_days:
            raise HTTPException(status_code=400, detail="Invalid delivery option")

        order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
        tracking_id = f"TRK{uuid.uuid4().hex[:8].upper()}"
        estimated_delivery = (
            datetime.utcnow() + timedelta(days=delivery_days[delivery_option])
        ).strftime("%Y-%m-%d")

        order_service = OrderService()
        calculated_pricing = await order_service.calculate_pricing_from_cart(cart, delivery_option)

        if abs(calculated_pricing.total - checkout_data.pricing.total) > 1:
            raise HTTPException(status_code=400, detail="Price mismatch. Please refresh cart and try again.")

        payment_service = PaymentService()
        payment_result = await payment_service.process_payment(
            order_id=order_id,
            payment_method=checkout_data.payment_method,
            payment_data=checkout_data.payment_data,
            amount=checkout_data.pricing.total,
            customer_info=checkout_data.customer_info,
            user=user
        )

        order = {
            "order_id": order_id,
            "email": user["email"],
            "customer_info": checkout_data.customer_info.model_dump(),
            "shipping_address": checkout_data.shipping_address.model_dump(),
            "items": cart,
            "pricing": checkout_data.pricing.model_dump(),
            "delivery_option": delivery_option,
            "payment_method": checkout_data.payment_method,
            "payment": {
                "status": payment_result["status"],
                "payment_id": payment_result.get("payment_id"),
                "transaction_id": payment_result.get("transaction_id"),
                "details": payment_result.get("details", {})
            },
            "shipping": {
                "tracking_id": tracking_id,
                "estimated_delivery": estimated_delivery,
                "status": "pending"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": payment_result["order_status"]
        }

        await orders_collection.insert_one(order)

        if payment_result["status"] in ["completed", "pending", "cod_confirmed"]:
            await users_collection.update_one(
                {"email": user["email"]},
                {"$set": {"cart": []}}
            )

        return CheckoutResponse(
            success=True,
            order_id=order_id,
            message=payment_result["message"],
            payment_url=payment_result.get("payment_url"),
            payment_id=payment_result.get("payment_id"),
            qr_code_url=payment_result.get("qr_code_url"),
            tracking_id=tracking_id,
            estimated_delivery=estimated_delivery,
            status=payment_result["order_status"],
            payment_instructions=payment_result.get("instructions"),
            payment_status=payment_result["status"],
            created_at=order["created_at"].isoformat(),
            updated_at=order["updated_at"].isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@router.get("/payment-methods/banks", status_code=200)
async def get_supported_banks() -> dict:
    return {
        "banks": [
            {"code": "SBI", "name": "State Bank of India"},
            {"code": "HDFC", "name": "HDFC Bank"},
            {"code": "ICICI", "name": "ICICI Bank"},
            {"code": "AXIS", "name": "Axis Bank"},
            {"code": "KOTAK", "name": "Kotak Mahindra Bank"},
            {"code": "PNB", "name": "Punjab National Bank"},
            {"code": "BOB", "name": "Bank of Baroda"},
            {"code": "CANARA", "name": "Canara Bank"},
            {"code": "UNION", "name": "Union Bank of India"},
            {"code": "IOB", "name": "Indian Overseas Bank"},
        ]
    }

@router.get("/payment-methods/upi-apps", status_code=200)
async def get_supported_upi_apps() -> dict:
    return {
        "upi_apps": [
            {"code": "GPAY", "name": "Google Pay"},
            {"code": "PHONEPE", "name": "PhonePe"},
            {"code": "PAYTM", "name": "Paytm"},
            {"code": "BHIM", "name": "BHIM UPI"},
            {"code": "AMAZONPAY", "name": "Amazon Pay"},
            {"code": "CRED", "name": "CRED UPI"},
            {"code": "MOBIKWIK", "name": "MobiKwik"},
        ]
    }

@router.post("/card", status_code=200)
async def card_checkout(data: CardPaymentRequest):
    # Simulate card payment logic
    if not data.card_number.startswith("4") or len(data.cvv) not in [3, 4]:
        raise HTTPException(status_code=402, detail="Payment failed")

    order_service = OrderService()
    order = await order_service.create_order(email=data.email, amount=data.amount, method="card")

    return {"message": "Payment successful", "order_id": order["id"]}
