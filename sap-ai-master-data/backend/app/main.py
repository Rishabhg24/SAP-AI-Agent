"""
Main FastAPI Application Entry Point for SAP AI Master Data Automation Platform.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.master_data import router as master_data_router
from app.api.rag import router as rag_router
from app.api.sap import router as sap_router
from app.api.validation import router as validation_router
from app.api.config_router import router as config_router
from app.api.agent import router as agent_router
from app.config import settings, check_and_auto_reload
from app.services.audit_service import init_db
from app.utils.logging import logger

# Initialize database
init_db()

# Auto-prime ChromaDB RAG Knowledge Base on startup if collection is empty
def _ensure_rag_indexed():
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.rag_db_path)
        col = client.get_or_create_collection(name=settings.rag_collection_name)
        if col.count() == 0:
            logger.info("ChromaDB knowledge collection is empty. Auto-ingesting SAP documentation...")
            from app.rag.ingest import ingest_documents
            ingest_documents()
    except Exception as e:
        logger.warning(f"Auto RAG indexing check note: {e}")

_ensure_rag_indexed()

app = FastAPI(
    title="SAP AI Master Data Automation Platform",
    description="Enterprise AI Assistant for Automated SAP Master Data Creation via Service Layer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Dynamic CORS Configuration from settings
allowed_origins = settings.parsed_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.netlify\.app|.*\.onrender\.com)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dynamic configuration hot-reload middleware: checks on-disk file changes before processing
@app.middleware("http")
async def dynamic_config_middleware(request: Request, call_next):
    check_and_auto_reload()
    return await call_next(request)

# Exception handlers for standardized error format
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err_msg = str(exc)
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {err_msg}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred while processing your request.",
            "errors": [err_msg]
        }
    )

# Register API Routers
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(validation_router)
app.include_router(sap_router)
app.include_router(master_data_router)
app.include_router(config_router)
app.include_router(agent_router)

@app.get("/api/health", tags=["Health"])
async def get_health():
    """Platform health check."""
    return {
        "success": True,
        "status": "HEALTHY",
        "message": "SAP AI Master Data Automation Platform Backend operational.",
        "data": {
            "version": "1.0.0",
            "environment": settings.environment,
            "sap_configured": settings.is_sap_configured,
            "nvidia_configured": settings.is_nvidia_configured,
            "rag_db": settings.rag_db_path
        }
    }

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

# Mount production frontend build for unified single-port execution
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "message": "SAP AI Master Data Automation Platform API",
            "docs": "/docs",
            "health": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
