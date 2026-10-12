from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import admin, auth, event, notifications, reports, support, teams
from app.database import Base, SessionLocal, engine
from app.migrate import migrate_schema
from app.seed import ensure_seed
from app.services.files import ensure_upload_dirs


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        # API returns JSON/files; browsers still benefit from CSP on error pages
        if "Cache-Control" not in response.headers and request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_upload_dirs()
    Base.metadata.create_all(bind=engine)
    migrate_schema(engine)
    db = SessionLocal()
    try:
        ensure_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="AppSec CTF API", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if not _origins:
    _origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,
)

app.include_router(auth.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(event.router, prefix="/api")
app.include_router(support.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
