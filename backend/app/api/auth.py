from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import TokenOut, UserCreate, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    get_user_by_username,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Логин уже занят")

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
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenOut:
    user = get_user_by_username(db, form.username.strip().lower())
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт отключён")
    return TokenOut(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
