from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import EventContent, Report, Team, User, UserRole
from app.schemas import ReportOut, ReportScoreUpdate, RubricScoreItem
from app.security import get_current_admin, get_current_user
from app.services.files import allowed_report_ext, resolve_path, save_upload
from app.services.notifications import notify_admins, notify_user

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_out(report: Report, viewer: User) -> ReportOut:
    is_admin = viewer.role == UserRole.admin
    can_view = is_admin or report.is_published
    return ReportOut(
        id=report.id,
        team_id=report.team_id,
        team_name=report.team.name,
        original_filename=report.original_filename,
        note=report.note,
        submitted_by=report.submitted_by.username,
        submitted_at=report.submitted_at,
        updated_at=report.updated_at,
        judge_id=report.judge_id if can_view else None,
        judge_username=report.judge.username if can_view and report.judge else None,
        rubric_scores=[RubricScoreItem(**x) for x in (report.rubric_scores or [])] if can_view else [],
        total_score=report.total_score if can_view else None,
        comment=report.comment if can_view else None,
        is_published=report.is_published,
        scored_at=report.scored_at if can_view else None,
        published_at=report.published_at if can_view else None,
        can_view_score=can_view and (report.total_score is not None or bool(report.comment)),
    )


def _load_report(db: Session, report_id: int) -> Report:
    report = (
        db.query(Report)
        .options(
            joinedload(Report.team),
            joinedload(Report.submitted_by),
            joinedload(Report.judge),
        )
        .filter(Report.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report


@router.post("/submit", response_model=ReportOut)
async def submit_report(
    file: UploadFile = File(...),
    note: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportOut:
    if not user.team_id:
        raise HTTPException(status_code=400, detail="Сначала вступите в команду")

    allowed_report_ext(file.filename or "")
    original, stored = await save_upload(
        file,
        "reports",
        allowed_exts={".pdf", ".docx", ".txt", ".md"},
    )

    report = db.query(Report).filter(Report.team_id == user.team_id).first()
    team = db.query(Team).filter(Team.id == user.team_id).first()

    if report:
        # replace file; reset publication so judge re-reviews
        try:
            old = resolve_path("reports", report.stored_name)
            old.unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass
        report.original_filename = original
        report.stored_name = stored
        report.content_type = file.content_type
        report.note = note
        report.submitted_by_id = user.id
        report.is_published = False
        report.published_at = None
        # keep draft scores but clear judge lock if reassigned later
    else:
        report = Report(
            team_id=user.team_id,
            original_filename=original,
            stored_name=stored,
            content_type=file.content_type,
            note=note,
            submitted_by_id=user.id,
        )
        db.add(report)

    notify_admins(
        db,
        "Новый отчёт",
        f"Команда «{team.name if team else user.team_id}» сдала/обновила отчёт",
        link="/admin/reports",
    )
    db.commit()
    db.refresh(report)
    return _report_out(_load_report(db, report.id), user)


@router.get("/mine", response_model=ReportOut | None)
def my_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReportOut | None:
    if not user.team_id:
        return None
    report = (
        db.query(Report)
        .options(
            joinedload(Report.team),
            joinedload(Report.submitted_by),
            joinedload(Report.judge),
        )
        .filter(Report.team_id == user.team_id)
        .first()
    )
    if not report:
        return None
    return _report_out(report, user)


@router.get("/rubric/default")
def default_rubric(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    content = db.query(EventContent).filter(EventContent.id == 1).first()
    return content.rubric if content else []


@router.get("", response_model=list[ReportOut])
def list_reports(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> list[ReportOut]:
    reports = (
        db.query(Report)
        .options(
            joinedload(Report.team),
            joinedload(Report.submitted_by),
            joinedload(Report.judge),
        )
        .order_by(Report.updated_at.desc())
        .all()
    )
    return [_report_out(r, admin) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportOut:
    report = _load_report(db, report_id)
    if user.role != UserRole.admin and user.team_id != report.team_id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    return _report_out(report, user)


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _load_report(db, report_id)
    if user.role != UserRole.admin and user.team_id != report.team_id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    path = resolve_path("reports", report.stored_name)
    return FileResponse(
        path,
        filename=report.original_filename,
        content_disposition_type="attachment",
    )


@router.post("/{report_id}/claim", response_model=ReportOut)
def claim_report(
    report_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ReportOut:
    report = _load_report(db, report_id)
    if report.judge_id and report.judge_id != admin.id:
        raise HTTPException(
            status_code=400,
            detail=f"Отчёт уже закреплён за судьёй @{report.judge.username if report.judge else report.judge_id}",
        )
    report.judge_id = admin.id
    db.commit()
    return _report_out(_load_report(db, report_id), admin)


@router.put("/{report_id}/score", response_model=ReportOut)
def score_report(
    report_id: int,
    payload: ReportScoreUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ReportOut:
    report = _load_report(db, report_id)
    if report.judge_id and report.judge_id != admin.id:
        raise HTTPException(status_code=403, detail="Отчёт закреплён за другим судьёй")

    content = db.query(EventContent).filter(EventContent.id == 1).first()
    expected = {item["id"]: item for item in (content.rubric if content else [])}
    if not expected:
        raise HTTPException(status_code=400, detail="Рубрика мероприятия не настроена")
    if len(payload.rubric_scores) != len(expected):
        raise HTTPException(status_code=400, detail="Оценка должна содержать все критерии рубрики")

    normalized = []
    for item in payload.rubric_scores:
        base = expected.get(item.id)
        if not base:
            raise HTTPException(status_code=400, detail=f"Неизвестный критерий: {item.id}")
        max_points = float(base["max_points"])
        if abs(item.max_points - max_points) > 0.01:
            raise HTTPException(status_code=400, detail=f"Неверный max_points для «{base['title']}»")
        if item.score < 0 or item.score > max_points:
            raise HTTPException(status_code=400, detail=f"Балл по «{base['title']}» вне диапазона")
        normalized.append(
            {
                "id": item.id,
                "title": base["title"],
                "max_points": max_points,
                "score": item.score,
                "description": base.get("description") or "",
            }
        )

    report.judge_id = admin.id
    report.rubric_scores = normalized
    report.total_score = round(sum(s["score"] for s in normalized), 2)
    report.comment = payload.comment
    report.scored_at = datetime.now(timezone.utc)

    if payload.publish:
        report.is_published = True
        report.published_at = datetime.now(timezone.utc)
        for member in report.team.members:
            notify_user(
                db,
                member.id,
                "Оценка опубликована",
                f"Результат по отчёту команды «{report.team.name}»: {report.total_score}/100",
                link="/report",
            )

    db.commit()
    return _report_out(_load_report(db, report_id), admin)


@router.post("/{report_id}/publish", response_model=ReportOut)
def publish_report(
    report_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ReportOut:
    report = _load_report(db, report_id)
    if report.judge_id and report.judge_id != admin.id:
        raise HTTPException(status_code=403, detail="Отчёт закреплён за другим судьёй")
    if report.total_score is None:
        raise HTTPException(status_code=400, detail="Сначала выставьте оценку")

    report.is_published = True
    report.published_at = datetime.now(timezone.utc)
    for member in report.team.members:
        notify_user(
            db,
            member.id,
            "Оценка опубликована",
            f"Результат по отчёту команды «{report.team.name}»: {report.total_score}/100",
            link="/report",
        )
    db.commit()
    return _report_out(_load_report(db, report_id), admin)

