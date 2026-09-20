import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile

from app.config import get_settings

# Magic signatures (offset, bytes)
_SIGNATURES: dict[str, list[tuple[int, bytes]]] = {
    ".pdf": [(0, b"%PDF")],
    ".docx": [(0, b"PK\x03\x04")],  # OOXML zip
    ".zip": [(0, b"PK\x03\x04"), (0, b"PK\x05\x06")],
    ".txt": [],  # validated as text
    ".md": [],
}


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


def _validate_magic(ext: str, data: bytes) -> None:
    if ext in (".txt", ".md"):
        if b"\x00" in data[:8192]:
            raise HTTPException(status_code=400, detail="Текстовый файл содержит бинарные данные")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="Текстовый файл должен быть в UTF-8") from exc
        return

    rules = _SIGNATURES.get(ext)
    if not rules:
        return
    if not any(data[start : start + len(sig)] == sig for start, sig in rules if len(data) >= start + len(sig)):
        raise HTTPException(status_code=400, detail=f"Содержимое файла не соответствует типу {ext}")


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
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Пустой файл")

    _validate_magic(ext, data)

    # Sanitize original filename for Content-Disposition later (store basename only)
    original = Path(file.filename).name.replace('"', "").replace("\n", "")[:200]

    stored = f"{uuid.uuid4().hex}{ext}"
    path = root / subdir / stored
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)

    return original, stored


def resolve_path(subdir: str, stored_name: str) -> Path:
    root = ensure_upload_dirs()
    # stored_name must be a single path segment (uuid + ext)
    if "/" in stored_name or "\\" in stored_name or stored_name in (".", ".."):
        raise HTTPException(status_code=400, detail="Некорректный путь")
    path = (root / subdir / stored_name).resolve()
    if not str(path).startswith(str((root / subdir).resolve())):
        raise HTTPException(status_code=400, detail="Некорректный путь")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return path
