import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Environment Variables
MONGO_URI = os.getenv("MONGO_URI")
ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"  # standard for JWT
ACCESS_EXPIRE_MINUTES = int(os.getenv("ACCESS_EXPIRE_MINUTES", 360))
REFRESH_EXPIRE_DAYS = int(os.getenv("REFRESH_EXPIRE_DAYS", 7))
