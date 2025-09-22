from typing import List
from models.checkout import CartItem, PricingSummary

class OrderService:
    
    async def calculate_pricing_from_cart(
        self, cart: List[CartItem], delivery_option: str
    ) -> PricingSummary:
        """
        Calculate total pricing based on cart items and delivery option.
        Includes subtotal, delivery fee, and total.
        """
        subtotal = sum(item.price * item.quantity for item in cart)
        delivery_fee = self._get_delivery_fee(delivery_option)
        total = subtotal + delivery_fee

        return PricingSummary(
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total
        )

    def _get_delivery_fee(self, option: str) -> float:
        """
        Return delivery fee based on selected option.
        """
        delivery_fees = {
            "standard": 40.0,
            "express": 80.0,
            "same-day": 120.0
        }
        return delivery_fees.get(option, 40.0)
