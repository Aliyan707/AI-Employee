"""
api/main.py — FastAPI application factory with lifespan management.

Startup: verify DB connection, initialize Kafka producer.
Shutdown: close connections.
Includes all routers with CORS for localhost:3000.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.logging import JSONLoggingMiddleware
from config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs startup tasks before yielding, shutdown tasks after.
    """
    # --- Startup ---
    logger.info("CS AI FTE starting up (environment=%s)", settings.environment)

    # Verify database connection
    from database.session import check_db_connection
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("DB connected ✓")
    else:
        logger.error("DB connection FAILED — check POSTGRES_* env vars")

    # Initialize Kafka producer (optional at startup — workers handle their own)
    try:
        from workers.kafka_client import get_kafka_producer
        producer = await get_kafka_producer()
        if producer:
            logger.info("Kafka producer initialized ✓")
        else:
            logger.warning("Kafka not available — running in direct mode")
    except Exception as e:
        logger.warning("Kafka initialization skipped: %s", e)

    yield

    # --- Shutdown ---
    logger.info("CS AI FTE shutting down...")
    try:
        from workers.kafka_client import close_kafka_producer
        await close_kafka_producer()
        logger.info("Kafka producer closed")
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title="CS AI FTE — Customer Success Agent",
    description="24/7 AI-powered customer success agent with multi-channel support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware ---
# JSON structured logging
app.add_middleware(JSONLoggingMiddleware)

# CORS for frontend (localhost:3000 in development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
from api.routers import webhooks, tickets, customers, reports

app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])


# --- Health check ---
@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "cs-fte", "version": "1.0.0"}
