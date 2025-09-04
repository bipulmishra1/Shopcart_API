import os
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from bson import ObjectId
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB client and collections
client = AsyncIOMotorClient(MONGO_URI)
db = client["fastapi_auth"]
products_collection = db["Project"]
users_collection = db["users"]
orders_collection = db["orders"]

# MongoDB ping on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    yield

# FastAPI application with lifespan
app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shopcart-shopping-website.onrender.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = "static"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount(f"/{STATIC_DIR}", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"message": "Favicon not found"})

@app.get("/")
async def read_root(request: Request):
    return {
        "message": "Welcome to the Bip Shop API!",
        "documentation_url": str(request.url.replace(path="/docs")),
        "health_check_url": request.url_for("health_check"),
        "api_resources": {
            "search": request.url_for("search_mobiles"),
            "user_cart": request.url_for("get_cart"),
            "user_wishlist": request.url_for("get_wishlist"),
            "login": request.url_for("login"),
            "signup": request.url_for("signup"),
        }
    }

@app.get("/home")
def home():
    return {"message": "Search API is running from MongoDB Atlas!"}

# Error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {exc}")
    raise HTTPException(status_code=500, detail="Internal Server Error")

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

ACCESS_SECRET_KEY = "access_secret_key"
REFRESH_SECRET_KEY = "refresh_secret_key"
ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 360
REFRESH_EXPIRE_DAYS = 7

# Models
class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class RemoveItem(BaseModel):
    product_id: str


# Utilities

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Auth Routes

@app.post("/signup", response_model=UserOut, status_code=201)
async def signup(user: UserIn):
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user.password)

    await users_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "hashed_password": hashed_pw,
        "refresh_token": None,
        "cart": [],
        "wishlist": []  
    })

    return UserOut(email=user.email)


@app.post("/login")
async def login(user: LoginRequest):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    await users_collection.update_one({"email": user.email}, {"$set": {"refresh_token": refresh_token}})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/refresh", response_model=Token)
async def refresh_token(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await users_collection.find_one({"email": email})
    if not user or user.get("refresh_token") != body.refresh_token:
        raise HTTPException(status_code=403, detail="Refresh token has expired or is invalid")

    new_access = create_access_token({"sub": email})
    new_refresh = create_refresh_token({"sub": email})
    await users_collection.update_one({"email": email}, {"$set": {"refresh_token": new_refresh}})
    return Token(access_token=new_access, token_type="bearer")

@app.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one({"email": current_user["email"]}, {"$set": {"refresh_token": None}})
    return {"message": "Logged out successfully"}

@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Welcome, {current_user['email']}! You are authenticated ✅"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Search Route
@app.get("/search/")
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
        doc["Product Photo"] = doc.get("Product Photo", "")
        results.append(doc)

# 🔢 Pagination Info
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



# Cart Routes
@app.post("/cart/add")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    try:
        product = await products_collection.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    # Fetch user's cart
    user = await users_collection.find_one({"email": current_user["email"]})
    cart = user.get("cart", [])

    # Normalize cart format
    normalized_cart = []
    for i in cart:
        if isinstance(i, str):
            normalized_cart.append({"product_id": i, "quantity": 1})
        else:
            normalized_cart.append(i)
    cart = normalized_cart

    # Add or update product in cart
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




# Remove item from cart

@app.post("/cart/remove")
async def remove_from_cart(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$pull": {"cart": {"product_id": item.product_id}}}


    )
    return {"message": "Product removed from cart"}

# View cart contents

@app.get("/cart")
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

                # Split photo links
                photo_str = product.get("Product Photo", "")
                product["Product Photo"] = photo_str.strip().split("\n")

                cart_items.append(product)
        except:
            continue

    return JSONResponse(content=cart_items)

# checkout cart clear


@app.post("/cart/checkout")
async def checkout(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    cart = user.get("cart", [])

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Create orders_collection if needed
    orders_collection = db["orders"]

    await orders_collection.insert_one({
        "email": user["email"],
        "items": cart,
        "timestamp": datetime.utcnow()
    })

    await users_collection.update_one(
        {"email": user["email"]},
        {"$set": {"cart": []}}
    )

    return {"message": "Checkout complete! Order saved."}

# Other cart-related routes...

@app.post("/cart/clear")
async def clear_cart(current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"cart": []}}
    )
    return {"message": "Cart cleared"}

# Add product to wishlist
@app.post("/wishlist/add")
async def add_to_wishlist(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$addToSet": {"wishlist": item.product_id}}  # avoids duplicates
    )
    return {"message": "Product added to wishlist"}

# Remove product from wishlist
@app.post("/wishlist/remove")
async def remove_from_wishlist(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$pull": {"wishlist": item.product_id}}
    )
    return {"message": "Product removed from wishlist"}

# wishlist ROUTE
@app.get("/wishlist")
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

    return JSONResponse(content=wishlist_items)

# Move item from wishlist to cart
@app.post("/wishlist/move-to-cart")
async def move_wishlist_to_cart(item: RemoveItem, current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    wishlist = user.get("wishlist", [])
    cart = user.get("cart", [])

    if item.product_id not in wishlist:
        raise HTTPException(status_code=404, detail="Product not in wishlist")

    # Normalize cart format
    normalized_cart = []
    for i in cart:
        if isinstance(i, str):
            normalized_cart.append({"product_id": i, "quantity": 1})
        else:
            normalized_cart.append(i)
    cart = normalized_cart

    # Add or update product in cart
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