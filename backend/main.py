import json
import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.routes import router
from backend.database import init_db


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(
    title="DocuQuery API",
    description="Document ingestion and grounded question answering API.",
    version="0.2.0",
    lifespan=lifespan,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docuquery")


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.exception(
            json.dumps(
                {
                    "event": "request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": elapsed_ms,
                }
            )
        )
        raise

    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": elapsed_ms,
            }
        )
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health_check():
    return {"status": "ok"}
