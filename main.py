from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.auth import router as auth_router
from router.cart import router as cart_router
from router.wishlist import router as wishlist_router
from router.search import router as search_router
from router.orders import router as orders_router
from router.payments import router as payments_router
from router.history import router as history_router


app = FastAPI()



@app.get("/")
def read_root():
    return {"message": "Welcome to Bipul's Shopping API!"}

@app.get("/ping")
def ping():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                    "https://your-frontend.com",
                    "https://shopcart-shopping-website.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount routers
app.include_router(auth_router, prefix="/auth")
app.include_router(cart_router, prefix="/cart")
app.include_router(wishlist_router, prefix="/wishlist")
app.include_router(search_router, prefix="/search")
app.include_router(orders_router, prefix="/orders")
app.include_router(payments_router, prefix="/pay")
app.include_router(history_router, prefix="/history")
