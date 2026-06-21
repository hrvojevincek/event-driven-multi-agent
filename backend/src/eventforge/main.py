from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eventforge import __version__
from eventforge.api.routes import health, v1
from eventforge.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="EventForge API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(v1.router, prefix="/api/v1", tags=["api"])
