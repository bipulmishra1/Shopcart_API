from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Import routers
from router.auth import router as auth_router
from router.cart import router as cart_router
from router.wishlist import router as wishlist_router
from router.search import router as search_router
from router.orders import router as orders_router
from router.payments import router as payments_router
from router.history import router as history_router
from router.checkout import router as checkout_router
from router.otp import router as otp_router

app = FastAPI(
    title="Bipul's Shopping API",
    description="Modular FastAPI backend for e-commerce features",
    version="1.0.0"
)

# Healthcheck and root
@app.get("/")
def read_root():
    return {"message": "Welcome to Bipul's Shopping API!"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://shopcart-shopping-website.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    print("🚀 Bipul's Shopping API is starting...")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 API shutting down gracefully.")

# Mount routers with tags for Swagger grouping
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(otp_router)
app.include_router(search_router, prefix="/search", tags=["Search"])
app.include_router(cart_router, prefix="/cart", tags=["Cart"])
app.include_router(wishlist_router, prefix="/wishlist", tags=["Wishlist"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(payments_router, prefix="/payment", tags=["Payments"])
app.include_router(history_router, prefix="/history", tags=["History"])
app.include_router(checkout_router, prefix="/checkout", tags=["Checkout"])




