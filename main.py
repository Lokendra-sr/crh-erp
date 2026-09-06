from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import Base, engine
from .routers import auth, clients, vendors, items

# Phase 1: create tables directly from the models on startup.
# Once the schema stabilizes, switch to Alembic migrations instead of this.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Canteen/Catering ERP",
    description="Phase 1: admins, clients, vendors, meals, purchases, inventory, expenses, billing, payments.",
    version="0.1.0",
)

# Allow the React dev server to call this API. Tighten this for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(vendors.router)
app.include_router(items.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
