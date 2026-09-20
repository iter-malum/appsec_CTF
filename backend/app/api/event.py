from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EventContent, User
from app.schemas import EventContentOut, EventContentUpdate, RubricItem
from app.security import get_current_admin, get_current_user
from app.services.files import resolve_path, save_upload

router = APIRouter(prefix="/event", tags=["event"])


def _get_content(db: Session) -> EventContent:
    content = db.query(EventContent).filter(EventContent.id == 1).first()
    if not content:
        raise HTTPException(status_code=404, detail="Контент мероприятия не найден")
    return content


def _out(content: EventContent) -> EventContentOut:
    rubric = [RubricItem(**item) for item in (content.rubric or [])]
    return EventContentOut(
        title=content.title,
        description_md=content.description_md,
        challenge_md=content.challenge_md,
        has_source=bool(content.source_stored_name),
        source_filename=content.source_filename,
        rubric=rubric,
        updated_at=content.updated_at,
    )


@router.get("", response_model=EventContentOut)
def get_event(db: Session = Depends(get_db)) -> EventContentOut:
    return _out(_get_content(db))


@router.put("", response_model=EventContentOut)
def update_event(
    payload: EventContentUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> EventContentOut:
    content = _get_content(db)
    if payload.title is not None:
        content.title = payload.title.strip()
    if payload.description_md is not None:
        content.description_md = payload.description_md
    if payload.challenge_md is not None:
        content.challenge_md = payload.challenge_md
    if payload.rubric is not None:
        total = sum(i.max_points for i in payload.rubric)
        if abs(total - 100) > 0.01:
            raise HTTPException(status_code=400, detail=f"Сумма критериев должна быть 100 (сейчас {total})")
        content.rubric = [i.model_dump() for i in payload.rubric]
    db.commit()
    db.refresh(content)
    return _out(content)


@router.post("/source", response_model=EventContentOut)
async def upload_source(
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> EventContentOut:
    content = _get_content(db)
    original, stored = await save_upload(file, "sources", allowed_exts={".zip"})
    if content.source_stored_name:
        try:
            resolve_path("sources", content.source_stored_name).unlink(missing_ok=True)
        except OSError:
            pass
    content.source_filename = original
    content.source_stored_name = stored
    db.commit()
    db.refresh(content)
    return _out(content)


@router.get("/source/download")
def download_source(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = _get_content(db)
    if not content.source_stored_name:
        raise HTTPException(status_code=404, detail="Исходники ещё не загружены")
    path = resolve_path("sources", content.source_stored_name)
    return FileResponse(path, filename=content.source_filename or "source.zip")
