"""
backend/main.py

Main FastAPI application entrypoint for The Lenny Growth Assistant.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logger, LoggingMiddleware
from app.db.session import init_db
from app.api.router import api_router

logger = setup_logger("lenny_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing persistence layer and database tables...")
    init_db()
    logger.info("The Lenny Growth Assistant Backend is ready.")
    yield
    # Shutdown
    logger.info("Shutting down Lenny Growth Assistant Backend.")

app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Conversational AI Assistant grounded strictly in Lenny's Podcast transcripts with Ship 30 essay generation and sandboxed Artifact viewing.",
    version="1.0.0",
    lifespan=lifespan
)

# Telemetry and logging middleware
app.add_middleware(LoggingMiddleware)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local React Vite frontend on any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")
app.include_router(api_router)  # Also mount at root for /health, /readiness, /config

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
