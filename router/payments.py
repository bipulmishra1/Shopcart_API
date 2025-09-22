from fastapi import APIRouter, Depends, HTTPException
from services.payment_service import PaymentService
from utils.tokens import get_current_user

router = APIRouter(tags=["Payments"])

@router.post("/verify", status_code=200)
async def verify_payment(
    order_id: str,
    payment_id: str,
    signature: str = None,
    current_user: dict = Depends(get_current_user)
):
    payment_service = PaymentService()
    result = await payment_service.verify_payment(order_id, payment_id, signature)

    if not result["verified"]:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    return {
        "message": "Payment verified successfully",
        "status": result["status"]
    }

# Optional: Add refund or webhook routes here later
