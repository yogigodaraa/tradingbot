import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    logger.info("Starting trading bot...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Paper trading: {settings.alpaca_paper}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # TODO: Start trading engine, data streams, scheduler
    logger.info("Trading bot ready")

    yield

    # Shutdown
    logger.info("Shutting down trading bot...")
    # TODO: Stop trading engine, close connections


app = FastAPI(
    title="Trading Bot API",
    description="AI-powered quantitative trading bot with live news detection and predictive algorithms",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "paper_trading": settings.alpaca_paper,
        "environment": settings.app_env,
    }


# Import and include API routers
from app.api.v1 import router as v1_router  # noqa: E402

app.include_router(v1_router, prefix="/api/v1")
