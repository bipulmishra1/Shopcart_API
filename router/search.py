from fastapi import APIRouter, Depends
from models.search import MobileSearchQuery
from database import products_collection

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

@router.get("/", status_code=200)
async def search_mobiles(query: MobileSearchQuery = Depends()):
    skip = (query.page - 1) * query.limit
    filters = {}

    if query.brand:
        filters["Brand"] = {"$regex": query.brand, "$options": "i"}
    if query.model:
        filters["Model"] = {"$regex": query.model, "$options": "i"}
    if query.color:
        filters["Color"] = {"$regex": query.color, "$options": "i"}
    if query.storage:
        filters["Storage"] = query.storage
    if query.memory:
        filters["Memory"] = query.memory
    if query.min_price is not None or query.max_price is not None:
        filters["Selling Price"] = {}
        if query.min_price is not None:
            filters["Selling Price"]["$gte"] = query.min_price
        if query.max_price is not None:
            filters["Selling Price"]["$lt"] = query.max_price

    sort_field = {
        "price": "Selling Price",
        "rating": "Rating"
    }.get(query.sort_by)

    cursor = products_collection.find(filters).skip(skip).limit(query.limit)
    if sort_field:
        cursor = cursor.sort(sort_field, 1 if query.order == "asc" else -1)

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["Product Photo"] = doc.get("Product Photo", "").strip().split("\n")
        results.append(doc)

    total = await products_collection.count_documents(filters)
    max_pages = (total + query.limit - 1) // query.limit

    return {
        "page": query.page,
        "limit": query.limit,
        "total_products": total,
        "max_pages": max_pages,
        "has_next": query.page < max_pages,
        "has_prev": query.page > 1,
        "products": results
    }
