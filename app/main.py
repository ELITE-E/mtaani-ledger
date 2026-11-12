import logging
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_engine

log = logging.getLogger(__name__)

app = FastAPI(title="Mtaani Express Ledger")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. Does not touch the database."""
    return {"status": "ok"}


@app.get("/health/db")
def health_db(engine: Annotated[Engine, Depends(get_engine)]) -> JSONResponse:
    """Readiness: the database answers a trivial query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        log.warning("database health check failed: %s", exc.__class__.__name__)
        return JSONResponse(status_code=503, content={"status": "error", "database": "down"})
    return JSONResponse(content={"status": "ok", "database": "up"})
