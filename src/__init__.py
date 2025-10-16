from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.main import init_db
from src.auth.routes import auth_router
from src.houses.routes import house_router
from src.booking.routes import booking_router
from src.reviews.routes import review_router
from src.scheduler.end_booking_email_scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server")
    await init_db()
    start_scheduler()
    yield
    print("Stopping server")

version = "v1"

app = FastAPI(
    lifespan=lifespan,
    version=version,
    description="An application for booking shortlets",
    docs_url=f"/api/{version}/docs",
    redoc_url=f"/api/{version}/redoc",
    contact={
        "name": "Quicklet support",
        "email": "oreelijah33@gmail.com"
    }
)
@app.get("/success")
async def success():
    return {"message": "Payment successful"}

app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=["auth"])
app.include_router(house_router, prefix=f"/api/{version}/houses", tags=["Houses"])
app.include_router(booking_router, prefix=f"/api/{version}/booking", tags=["Bookings"])
app.include_router(review_router, prefix=f"/api/{version}/reviews", tags=["reviews"])