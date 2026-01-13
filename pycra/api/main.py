try:
    from contextlib import asynccontextmanager
except ImportError:
    from contextlib2 import asynccontextmanager # type: ignore
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from pycra.api.middleware import register_exception_handlers
from pycra import settings
from pycra.utils import setup_logger
from pycra.api.core import get_factory
from pycra.api.router import cckg_router
import uvicorn
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
api_logger = setup_logger(name="pycra-api")

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    api_logger.info("Starting the pycra API service...")
    await get_factory()
    api_logger.info("pycra API service started successfully")
    try:
        yield
    finally:
        api_logger.info("The pycra API service is shut down")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.name,
        description="Welcome to pycra: a Contract Review Agent",
        version=settings.app.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins="*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    
    # Include routers
    app.include_router(cckg_router, prefix=settings.app.api_prefix)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "pycra API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": getattr(settings.app, "version", "1.0.0")
        }

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "pycra.api.main:app", 
        host=settings.server.host, 
        port=settings.server.port, 
        reload=settings.app.debug
    )
