from fastapi import APIRouter, Depends
from models.schemas import Card, CardRemove, DefaultCard
from database import users_collection
from utils.tokens import get_current_user
from uuid import uuid4

router = APIRouter()

@router.post("/cards/add")
async def add_card(card: Card, current_user: dict = Depends(get_current_user)):
    card_entry = {
        "card_id": str(uuid4()),
        "last4": card.last4,
        "brand": card.brand,
        "expiry": card.expiry
    }
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$push": {"cards": card_entry}}
    )
    return {"message": "Card added", "card": card_entry}

@router.post("/cards/remove")
async def remove_card(data: CardRemove, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$pull": {"cards": {"card_id": data.card_id}}}
    )
    return {"message": "Card removed"}

@router.get("/cards")
async def list_cards(current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_user["email"]})
    return {"cards": user.get("cards", [])}

@router.post("/cards/set-default")
async def set_default_card(data: DefaultCard, current_user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"default_card": data.card_id}}
    )
    return {"message": "Default card set"}
