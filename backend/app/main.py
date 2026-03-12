"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api import generate, artwork
from app.core.config import CORS_ORIGINS, OUTPUTS_DIR
from app.db.database import init_db


# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Exquisite Corpse Generator API",
    description="API for generating three-part composite images from The Met collection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router)
app.include_router(artwork.router)

# Serve static files (outputs)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "exquisite-corpse-api"}


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Exquisite Corpse Generator API",
        "docs": "/docs",
        "health": "/health"
    }
