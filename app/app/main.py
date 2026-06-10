import os
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.core.config import settings
from src.api.router import router as api_router
from src.monitoring.metrics import REGISTRY

# Structured JSON logging — enabled when LOG_FORMAT=json (default in production)
if os.getenv("LOG_FORMAT", "json") == "json":
    from src.monitoring.json_logging import setup_json_logging
    setup_json_logging(
        level=int(os.getenv("LOG_LEVEL", "20")),  # 20=INFO
        service_name="vbq-api",
        log_file=os.getenv("LOG_FILE"),
    )

app = FastAPI(
    title="VBQ-UNIFIED API",
    description="Quantitative Value Betting System API (NBA, Football, MMA)",
    version="4.0.0"
)

app.include_router(api_router)

# CORS configuration
allowed_origins = [
    origin.strip() 
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    if origin.strip()
]

# Reject startup with open CORS in production
if settings.ENVIRONMENT.lower() in ("production", "staging", "live") and (not allowed_origins or allowed_origins == ["*"]):
    raise RuntimeError(
        "SECURITY: ALLOWED_ORIGINS must be explicitly set to specific domains in production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT if hasattr(settings, "ENVIRONMENT") else "development",
        "timestamp": time.time()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint — real instrumented metrics."""
    content = generate_latest(REGISTRY)
    return PlainTextResponse(content=content, media_type=CONTENT_TYPE_LATEST)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "HTTPException"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "type": "GenericException"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
