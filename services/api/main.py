import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from fleetguard_db.database import check_postgres, close_database_engine
from fleetguard_db.mongo import check_mongodb, close_mongo_client
from fleetguard_db.redis_cache import check_redis, close_redis_client

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fleetguard.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_database_engine()
    close_mongo_client()
    close_redis_client()


app = FastAPI(title="FleetGuard API", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    logger.debug("Health check requested")
    return {"status": "ok", "service": "api"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    try:
        check_postgres()
        check_mongodb()
        check_redis()
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="database dependencies unavailable") from exc
    return {"status": "ready", "service": "api"}