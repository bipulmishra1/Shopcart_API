from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime
from database import users_collection
from utils.otp import generate_otp, get_expiry
from utils.email import send_email  # ✅ Email sending is active

router = APIRouter(prefix="/api/v1/otp", tags=["OTP"])

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

@router.post("/request", status_code=200)
async def request_otp(data: OTPRequest):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()
    expiry = get_expiry()

    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"otp": otp, "otp_expires": expiry}}
    )

    # ✅ Send OTP via email
    send_email(to=data.email, subject="Your OTP", body=f"Your OTP is: {otp}")
    print(f"Sent OTP {otp} to {data.email}")  # Optional: for debugging

    return {"message": "OTP sent successfully"}

@router.post("/verify", status_code=200)
async def verify_otp(data: OTPVerify):
    user = await users_collection.find_one({"email": data.email})
    if not user or user.get("otp") != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.utcnow() > user.get("otp_expires"):
        raise HTTPException(status_code=400, detail="OTP expired")

    return {"message": "OTP verified"}
