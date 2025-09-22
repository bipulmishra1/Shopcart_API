from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from models.wishlist import RemoveItem, WishlistItem
from database import users_collection, products_collection
from utils.tokens import get_current_user
from typing import List

router = APIRouter(prefix="/api/v1/wishlist", tags=["Wishlist"])

# ✅ Add product to wishlist
@router.post("/add", status_code=200)
async def add_to_wishlist(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$addToSet": {"wishlist": item.product_id}}
    )
    return {"message": "Product added to wishlist"}

# ✅ Remove product from wishlist
@router.post("/remove", status_code=200)
async def remove_from_wishlist(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$pull": {"wishlist": item.product_id}}
    )
    return {"message": "Product removed from wishlist"}

# ✅ Get wishlist items
@router.get("/", response_model=List[WishlistItem], status_code=200)
async def get_wishlist(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    product_ids = user.get("wishlist", [])
    wishlist_items = []

    for pid in product_ids:
        product = await products_collection.find_one({"_id": ObjectId(pid)})
        if product:
            wishlist_items.append(WishlistItem(
                product_id=str(product["_id"]),
                name=product["Name"],
                price=product["Selling Price"],
                image_url=product["Product Photo"].strip().split("\n")[0]
            ))

    return wishlist_items

# ✅ Move product from wishlist to cart
@router.post("/move-to-cart", status_code=200)
async def move_wishlist_to_cart(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wishlist = user.get("wishlist", [])
    cart = user.get("cart", [])

    if item.product_id not in wishlist:
        raise HTTPException(status_code=404, detail="Product not in wishlist")

    for i in cart:
        if i["product_id"] == item.product_id:
            i["quantity"] += 1
            break
    else:
        cart.append({"product_id": item.product_id, "quantity": 1})

    await users_collection.update_one(
        {"email": current_user["email"]},
        {
            "$set": {"cart": cart},
            "$pull": {"wishlist": item.product_id}
        }
    )

    return {"message": "Product moved to cart"}
