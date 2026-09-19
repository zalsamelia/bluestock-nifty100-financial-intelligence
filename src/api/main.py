"""
FastAPI Main Application Entry Point (Sprint 6 — Day 38).

Features:
- 16 High-Performance Institutional REST Endpoints
- Prefix: /api/v1
- CORS Middleware (Allow all origins for internal integration)
- Request Logging & Timing Middleware
- OpenAPI 3.0 Documentation at /docs and /redoc
- Exportable OpenAPI JSON & Postman Collection
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.api.routers import health, companies, screener, sectors, peers, valuation, portfolio, documents

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

# Setup Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nifty100_api")

app = FastAPI(
    title="Bluestock Nifty 100 Financial Intelligence API",
    description="Institutional-grade REST API providing real-time financial ratios, DuPont drivers, Screener queries, Sector benchmarks, and ReportLab PDF tearsheets for the Nifty 100 universe.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request Timing & Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = round((time.time() - start_time) * 1000.0, 2)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} ({process_time_ms} ms)")
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    return response


# 3. Mount Routers with /api/v1 Prefix
API_V1_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(companies.router, prefix=API_V1_PREFIX)
app.include_router(screener.router, prefix=API_V1_PREFIX)
app.include_router(sectors.router, prefix=API_V1_PREFIX)
app.include_router(peers.router, prefix=API_V1_PREFIX)
app.include_router(valuation.router, prefix=API_V1_PREFIX)
app.include_router(portfolio.router, prefix=API_V1_PREFIX)
app.include_router(documents.router, prefix=API_V1_PREFIX)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to OpenAPI Swagger documentation."""
    return RedirectResponse(url="/docs")


def export_openapi_and_postman():
    """Export OpenAPI 3.0 specification JSON and Postman collection."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. OpenAPI JSON
    openapi_schema = app.openapi()
    openapi_file = DOCS_DIR / "openapi.json"
    with open(openapi_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI spec to: {openapi_file}")

    # 2. Postman Collection JSON
    postman_items = []
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, op in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete"]:
                continue
            item = {
                "name": op.get("summary", path),
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": f"http://localhost:8000{path}",
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": [p for p in path.strip("/").split("/") if p]
                    },
                    "description": op.get("description", "")
                }
            }
            postman_items.append(item)

    postman_collection = {
        "info": {
            "name": "Bluestock Nifty 100 Intelligence API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Postman collection for the 16 Nifty 100 Financial Intelligence REST endpoints."
        },
        "item": postman_items
    }

    postman_file = DOCS_DIR / "postman_collection.json"
    with open(postman_file, "w", encoding="utf-8") as f:
        json.dump(postman_collection, f, indent=2)
    print(f"Exported Postman Collection to: {postman_file}")


if __name__ == "__main__":
    import uvicorn
    export_openapi_and_postman()
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
