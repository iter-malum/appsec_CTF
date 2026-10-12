from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import EventContent, User, UserRole
from app.rate_limit import client_ip, limiter
from app.schemas import TokenOut, UserCreate, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    get_user_by_username,
    hash_password,
    verify_password,
)
from app.services.event_time import event_is_finished

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    limiter.check(
        f"reg:{client_ip(request)}:{payload.username}",
        settings.rate_limit_register,
        settings.rate_limit_window_sec,
    )

    content = db.query(EventContent).filter(EventContent.id == 1).first()
    if content and event_is_finished(content):
        raise HTTPException(status_code=403, detail="Регистрация закрыта: мероприятие завершено")

    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Логин уже занят")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
        university=payload.university,
        course=payload.course,
        study_program=payload.study_program,
        contact_extra=payload.contact_extra,
        role=UserRole.participant,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    uname = form.username.strip().lower()[:64]
    limiter.check(
        f"login:{client_ip(request)}:{uname}",
        settings.rate_limit_login,
        settings.rate_limit_window_sec,
    )

    user = get_user_by_username(db, uname)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт отключён")
    return TokenOut(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
