from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from models.schemas import RemoveItem
from database import users_collection, products_collection
from utils.tokens import get_current_user

router = APIRouter()

@router.post("/add")
async def add_to_wishlist(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$addToSet": {"wishlist": item.product_id}}
    )
    return {"message": "Product added to wishlist"}

@router.post("/remove")
async def remove_from_wishlist(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$pull": {"wishlist": item.product_id}}
    )
    return {"message": "Product removed from wishlist"}

@router.get("/")
async def get_wishlist(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    product_ids = user.get("wishlist", [])
    wishlist_items = []
    for pid in product_ids:
        product = await products_collection.find_one({"_id": ObjectId(pid)})
        if product:
            product["_id"] = str(product["_id"])
            product["Product Photo"] = product.get("Product Photo", "").strip().split("\n")
            wishlist_items.append(product)
    return {"wishlist": wishlist_items}

@router.post("/move-to-cart")
async def move_wishlist_to_cart(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    wishlist = user.get("wishlist", [])
    cart = user.get("cart", [])

    if item.product_id not in wishlist:
        raise HTTPException(status_code=404, detail="Product not in wishlist")

    normalized_cart = []
    for i in cart:
        if isinstance(i, str):
            normalized_cart.append({"product_id": i, "quantity": 1})
        else:
            normalized_cart.append(i)
    cart = normalized_cart

    for i in cart:
        if i["product_id"] == item.product_id:
            i["quantity"] += 1
            break
    else:
        cart.append({"product_id": item.product_id, "quantity": 1})

    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"cart": cart}, "$pull": {"wishlist": item.product_id}}
    )

    return {"message": "Item moved from wishlist to cart"}
