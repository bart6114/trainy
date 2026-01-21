"""FastAPI application for Trainy."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_v1_router

app = FastAPI(
    title="Trainy",
    description="Training tracking web application",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API router
app.include_router(api_v1_router)
