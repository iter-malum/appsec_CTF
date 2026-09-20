from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Team, User, UserRole
from app.schemas import AdminUserCreate, UserOut
from app.security import get_current_admin, get_user_by_username, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> User:
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Логин уже занят")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
        role=UserRole.admin if payload.role == "admin" else UserRole.participant,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя отключить себя")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/teams")
def list_teams(_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> list[dict]:
    teams = db.query(Team).order_by(Team.created_at.desc()).all()
    result = []
    for t in teams:
        result.append(
            {
                "id": t.id,
                "name": t.name,
                "owner_id": t.owner_id,
                "members": [
                    {"id": m.id, "username": m.username, "display_name": m.display_name}
                    for m in t.members
                ],
                "created_at": t.created_at,
            }
        )
    return result
