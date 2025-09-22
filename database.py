from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(MONGO_URI)
db = client["fastapi_auth"]
products_collection = db["Product"]
users_collection = db["users"]
orders_collection = db["orders"]


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["your_db_name"]
orders_collection = db["orders"]
