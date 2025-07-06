import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.routes import messages, summaries
from app.utils.config import settings
from app.utils.cache import cache_manager

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup: Initialize cache
    logger.info("Starting up application...")
    await cache_manager.initialize()
    
    yield  # Application runs here
    
    # Shutdown: Clean up resources
    logger.info("Shutting down application...")
    # Add any cleanup code here if needed

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Nova Chatbot API",
        description="Backend API for Nova - A Human-Mimicking, Memory-Aware Chatbot",
        version="0.1.0",
        debug=settings.debug,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add cache control headers middleware
    @app.middleware("http")
    async def add_cache_control_header(request: Request, call_next):
        response = await call_next(request)
        if request.method == "GET" and "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = f"public, max-age={settings.cache_ttl}"
        return response

    # Include routers
    app.include_router(
        messages.router,
        prefix=f"{settings.api_prefix}/messages",
        tags=["messages"]
    )
    app.include_router(
        summaries.router,
        prefix=f"{settings.api_prefix}/summaries",
        tags=["summaries"]
    )
    
    return app

# Create the FastAPI application
app = create_application()


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request, exc):
    logger.error(f"Pydantic validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


@app.get("/")
async def root():
    return {
        "name": "Nova Chatbot API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}