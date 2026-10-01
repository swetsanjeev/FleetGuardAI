import logging
import os

from fastapi import FastAPI

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fleetguard.simulator")
app = FastAPI(title="FleetGuard Simulator", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    logger.debug("Health check requested")
    return {"status": "ok", "service": "simulator"}