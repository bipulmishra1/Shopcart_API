from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from models.cart import CartItem, CartProduct, CartResponse, CartTotals
from database import users_collection, products_collection
from utils.tokens import get_current_user

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])

@router.post("/add", status_code=200)
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    product = await products_collection.find_one({"_id": ObjectId(item.product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    user = await users_collection.find_one({"email": current_user["email"]})
    cart = user.get("cart", [])

    for i in cart:
        if i["product_id"] == item.product_id:
            i["quantity"] = item.quantity
            break
    else:
        cart.append({"product_id": item.product_id, "quantity": item.quantity})

    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"cart": cart}}
    )

    return {"message": f"Added {item.quantity} unit(s) to cart"}

@router.get("/", response_model=CartResponse, status_code=200)
async def get_cart(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    raw_cart = user.get("cart", [])
    cart_items = []
    subtotal = 0.0

    for item in raw_cart:
        product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})
        if product:
            product_id = str(product["_id"])
            name = product.get("name", "")
            price = float(product.get("price", 0))
            quantity = item["quantity"]
            image_urls = product.get("Product Photo", "").strip().split("\n")

            subtotal += price * quantity

            cart_items.append(CartProduct(
                product_id=product_id,
                name=name,
                price=price,
                quantity=quantity,
                image_urls=image_urls
            ))

    delivery_fee = 50.0 if subtotal < 500 else 0.0
    total = subtotal + delivery_fee

    return CartResponse(
        cart=cart_items,
        totals=CartTotals(
            subtotal=round(subtotal, 2),
            delivery_fee=round(delivery_fee, 2),
            total=round(total, 2)
        )
    )

@router.post("/clear", status_code=200)
async def clear_cart(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"cart": []}}
    )
    return {"message": "Cart cleared"}
