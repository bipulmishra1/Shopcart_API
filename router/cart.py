from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from fastapi.responses import JSONResponse
from datetime import datetime
from models.schemas import CartItem
from database import users_collection, products_collection
from utils.tokens import get_current_user

router = APIRouter()

@router.post("/add")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    try:
        product = await products_collection.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        print(f"Invalid product ID: {e}")
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    user = await users_collection.find_one({"email": current_user["email"]})
    cart = user.get("cart", [])

    # Normalize cart structure
    normalized_cart = []
    for i in cart:
        if isinstance(i, str):
            normalized_cart.append({"product_id": i, "quantity": 1})
        else:
            normalized_cart.append(i)
    cart = normalized_cart

    # Update quantity or add new item
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

@router.get("/")
async def get_cart(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    raw_cart = user.get("cart", [])
    cart_items = []

    for item in raw_cart:
        try:
            product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})
            if product:
                product["_id"] = str(product["_id"])
                product["quantity"] = item["quantity"]
                product["Product Photo"] = product.get("Product Photo", "").strip().split("\n")
                cart_items.append(product)
        except Exception as e:
            print(f"Error loading cart item: {e}")
            continue

    return {"cart": cart_items}

@router.post("/clear")
async def clear_cart(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"cart": []}}
    )
    return {"message": "Cart cleared"}
