import uuid
import qrcode
import io
import base64
import logging
from typing import Dict, Any, Union
from fastapi import HTTPException
from models.checkout import (
    PaymentMethod,
    CardPaymentData,
    UPIPaymentData,
    NetBankingPaymentData,
    CODPaymentData
)

logger = logging.getLogger(__name__)

class PaymentService:
    
    async def process_payment(
        self, 
        order_id: str, 
        payment_method: PaymentMethod,
        payment_data: Union[
            CardPaymentData,
            UPIPaymentData,
            NetBankingPaymentData,
            CODPaymentData
        ],
        amount: float,
        customer_info: dict,
        user: dict
    ) -> Dict[str, Any]:
        logger.info(f"Processing payment for order {order_id} via {payment_method}")
        
        if payment_method == PaymentMethod.CARD:
            return await self._process_card_payment(order_id, payment_data, amount, customer_info, user)
        elif payment_method == PaymentMethod.UPI:
            return await self._process_upi_payment(order_id, payment_data, amount, customer_info)
        elif payment_method == PaymentMethod.NETBANKING:
            return await self._process_netbanking_payment(order_id, payment_data, amount, customer_info)
        elif payment_method == PaymentMethod.COD:
            return await self._process_cod_payment(order_id, amount, customer_info)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported payment method: {payment_method}")
    
    async def _process_card_payment(
        self, order_id: str, payment_data: CardPaymentData, 
        amount: float, customer_info: dict, user: dict
    ) -> Dict[str, Any]:
        if payment_data.card_id:
            saved_cards = user.get("cards", [])
            card = next((c for c in saved_cards if c.get("card_id") == payment_data.card_id), None)
            if not card:
                raise HTTPException(status_code=400, detail="Invalid payment card")
            transaction_id = f"txn_card_{uuid.uuid4().hex[:8]}"
            return {
                "status": "completed",
                "order_status": "confirmed",
                "transaction_id": transaction_id,
                "payment_id": f"pay_card_{uuid.uuid4().hex[:8]}",
                "message": f"Payment successful using {card.get('brand', 'your')} card ending in {card.get('last4', '****')}"
            }
        else:
            transaction_id = f"txn_card_{uuid.uuid4().hex[:8]}"
            payment_url = f"https://payments.example.com/pay/{order_id}"
            return {
                "status": "pending",
                "order_status": "pending_payment",
                "transaction_id": transaction_id,
                "payment_id": f"pay_card_{uuid.uuid4().hex[:8]}",
                "payment_url": payment_url,
                "message": "Please complete payment on secure payment page",
                "instructions": "You will be redirected to complete your card payment"
            }
    
    async def _process_upi_payment(
        self, order_id: str, payment_data: UPIPaymentData, 
        amount: float, customer_info: dict
    ) -> Dict[str, Any]:
        payment_id = f"upi_{uuid.uuid4().hex[:8]}"
        upi_string = f"upi://pay?pa=merchant@ybl&pn=Shopcart&am={amount}&cu=INR&tn=Order-{order_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_base64}"
        return {
            "status": "pending",
            "order_status": "pending_payment", 
            "payment_id": payment_id,
            "qr_code_url": qr_code_url,
            "payment_url": f"https://payments.example.com/upi/{payment_id}",
            "message": "Scan QR code or use UPI app to complete payment",
            "instructions": f"Pay ₹{amount} using any UPI app by scanning the QR code"
        }
    
    async def _process_netbanking_payment(
        self, order_id: str, payment_data: NetBankingPaymentData,
        amount: float, customer_info: dict
    ) -> Dict[str, Any]:
        payment_id = f"nb_{uuid.uuid4().hex[:8]}"
        payment_url = f"https://payments.example.com/netbanking/{payment_data.bank_code}/{payment_id}"
        return {
            "status": "pending",
            "order_status": "pending_payment",
            "payment_id": payment_id,
            "payment_url": payment_url,
            "message": f"Complete payment using {payment_data.bank_name} net banking",
            "instructions": f"You will be redirected to {payment_data.bank_name} secure banking page"
        }
    
    async def _process_cod_payment(
        self, order_id: str, amount: float, customer_info: dict
    ) -> Dict[str, Any]:
        return {
            "status": "cod_confirmed",
            "order_status": "confirmed",
            "payment_id": f"cod_{uuid.uuid4().hex[:8]}",
            "message": f"Order confirmed! Pay ₹{amount} when delivered",
            "instructions": "Please keep exact change ready for delivery"
        }

    async def verify_payment(
        self, order_id: str, payment_id: str, signature: str = None
    ) -> Dict[str, Any]:
        return {
            "verified": True,
            "status": "completed"
        }
