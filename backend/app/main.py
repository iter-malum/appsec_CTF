from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, event, notifications, reports, support, teams
from app.database import Base, SessionLocal, engine
from app.seed import ensure_seed
from app.services.files import ensure_upload_dirs


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_upload_dirs()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="AppSec CTF API", version="1.0.0", lifespan=lifespan)

# Same-origin через Next (:3000) / Caddy — credentials нужны для cookie
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
