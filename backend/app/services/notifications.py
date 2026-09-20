from sqlalchemy.orm import Session

from app.models import Notification, User, UserRole


def notify_user(
    db: Session,
    user_id: int,
    title: str,
    body: str,
    link: str | None = None,
) -> Notification:
    n = Notification(user_id=user_id, title=title, body=body, link=link)
    db.add(n)
    return n


def notify_admins(
    db: Session,
    title: str,
    body: str,
    link: str | None = None,
    exclude_user_id: int | None = None,
) -> None:
    admins = db.query(User).filter(User.role == UserRole.admin, User.is_active.is_(True)).all()
    for admin in admins:
        if exclude_user_id and admin.id == exclude_user_id:
            continue
        notify_user(db, admin.id, title, body, link)
