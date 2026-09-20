import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile

from app.config import get_settings


def ensure_upload_dirs() -> Path:
    settings = get_settings()
    root = Path(settings.upload_dir)
    (root / "reports").mkdir(parents=True, exist_ok=True)
    (root / "sources").mkdir(parents=True, exist_ok=True)
    return root


def allowed_report_ext(filename: str) -> str:
    settings = get_settings()
    ext = Path(filename).suffix.lower()
    allowed = {e.strip().lower() for e in settings.allowed_report_extensions.split(",") if e.strip()}
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Допустимые форматы: {', '.join(sorted(allowed))}",
        )
    return ext


async def save_upload(file: UploadFile, subdir: str, allowed_exts: set[str] | None = None) -> tuple[str, str]:
    settings = get_settings()
    root = ensure_upload_dirs()
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл без имени")

    ext = Path(file.filename).suffix.lower()
    if allowed_exts is not None and ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Недопустимый тип файла: {ext}")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Максимальный размер файла: {settings.max_upload_mb} МБ")

    stored = f"{uuid.uuid4().hex}{ext}"
    path = root / subdir / stored
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)

    return file.filename, stored


def resolve_path(subdir: str, stored_name: str) -> Path:
    root = ensure_upload_dirs()
    path = (root / subdir / stored_name).resolve()
    if not str(path).startswith(str((root / subdir).resolve())):
        raise HTTPException(status_code=400, detail="Некорректный путь")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return path
