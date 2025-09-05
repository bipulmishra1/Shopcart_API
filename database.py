from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["fastapi_auth"]
products_collection = db["Product"]
users_collection = db["users"]
orders_collection = db["orders"]
