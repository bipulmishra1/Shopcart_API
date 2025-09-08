from fastapi import APIRouter, Query
from typing import Optional
from database import products_collection
from bson import ObjectId

router = APIRouter(tags=["Search"])

# 🔍 Search mobiles with filters, sorting, and pagination
@router.get("/")
async def search_mobiles(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    storage: Optional[str] = Query(None),
    memory: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    order: Optional[str] = Query("asc"),
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0)
):
    skip = (page - 1) * limit
    query = {}

    if brand:
        query["Brand"] = {"$regex": brand, "$options": "i"}
    if model:
        query["Model"] = {"$regex": model, "$options": "i"}
    if color:
        query["Color"] = {"$regex": color, "$options": "i"}
    if storage:
        query["Storage"] = storage
    if memory:
        query["Memory"] = memory
    if min_price is not None and max_price is not None:
        query["Selling Price"] = {"$gte": min_price, "$lt": max_price}
    elif min_price is not None:
        query["Selling Price"] = {"$gte": min_price}
    elif max_price is not None:
        query["Selling Price"] = {"$lt": max_price}

    sort_field = None
    if sort_by == "price":
        sort_field = "Selling Price"
    elif sort_by == "rating":
        sort_field = "Rating"

    cursor = products_collection.find(query).skip(skip).limit(limit)
    if sort_field:
        cursor = cursor.sort(sort_field, 1 if order == "asc" else -1)

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["Product Photo"] = doc.get("Product Photo", "").strip().split("\n")
        results.append(doc)

    total = await products_collection.count_documents(query)
    max_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total_products": total,
        "max_pages": max_pages,
        "has_next": page < max_pages,
        "has_prev": page > 1,
        "products": results
    }

# 🔠 Autocomplete brand suggestions
@router.get("/brands/autocomplete")
async def suggest_brands(prefix: str = Query("", min_length=0)):
    pipeline = [
        {"$match": {"Brand": {"$regex": f"^{prefix}", "$options": "i"}}},
        {"$group": {"_id": "$Brand"}},
        {"$limit": 10}
    ]
    cursor = products_collection.aggregate(pipeline)
    return [doc["_id"] async for doc in cursor]
