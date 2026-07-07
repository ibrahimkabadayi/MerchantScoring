"""
Moka Fit Score — FastAPI Application Entry Point

Initializes the app, mounts routers, and configures CORS.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize database tables. Shutdown: cleanup."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
from api.routes.merchants import router as merchants_router
from api.routes.outreach import router as outreach_router

app.include_router(merchants_router)
app.include_router(outreach_router)


@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
    }
