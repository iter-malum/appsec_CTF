from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User, UserRole
from app.rate_limit import client_ip, limiter
from app.schemas import TokenOut, UserCreate, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    get_user_by_username,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.cookie_name, path="/")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    limiter.check(f"reg:{client_ip(request)}", settings.rate_limit_register, settings.rate_limit_window_sec)
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Не удалось зарегистрироваться. Проверьте данные.")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
        role=UserRole.participant,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    response: Response,
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    limiter.check(f"login:{client_ip(request)}", settings.rate_limit_login, settings.rate_limit_window_sec)
    limiter.check(
        f"login-user:{form.username.strip().lower()}",
        settings.rate_limit_login,
        settings.rate_limit_window_sec,
    )

    user = get_user_by_username(db, form.username.strip().lower())
    dummy = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    if user:
        valid = verify_password(form.password, user.password_hash)
    else:
        verify_password(form.password, dummy)
        valid = False

    if not user or not valid or not user.is_active:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    token = create_access_token(user.username)
    _set_cookie(response, token)
    return TokenOut(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    _clear_cookie(response)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
