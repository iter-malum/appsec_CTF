from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _clean_text(v: str, field: str) -> str:
    v = " ".join(v.strip().split())
    if not v:
        raise ValueError(f"Поле «{field}» обязательно")
    if any(ch in v for ch in ("<", ">", "{", "}", "\x00")):
        raise ValueError(f"Недопустимые символы в поле «{field}»")
    return v


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=128)
    university: str = Field(min_length=2, max_length=256)
    course: str = Field(min_length=1, max_length=64)
    study_program: str = Field(min_length=2, max_length=256)
    contact_extra: str = Field(min_length=3, max_length=256)

    @field_validator("username")
    @classmethod
    def username_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Логин: только латиница, цифры, _ и -")
        return v

    @field_validator("display_name")
    @classmethod
    def display_ok(cls, v: str) -> str:
        return _clean_text(v, "Отображаемое имя")

    @field_validator("university")
    @classmethod
    def university_ok(cls, v: str) -> str:
        return _clean_text(v, "ВУЗ")

    @field_validator("course")
    @classmethod
    def course_ok(cls, v: str) -> str:
        return _clean_text(v, "Курс")

    @field_validator("study_program")
    @classmethod
    def program_ok(cls, v: str) -> str:
        return _clean_text(v, "Направление подготовки")

    @field_validator("contact_extra")
    @classmethod
    def contact_ok(cls, v: str) -> str:
        return _clean_text(v, "Доп. связь")


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=128)
    role: str = "admin"

    @field_validator("username")
    @classmethod
    def username_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Логин: только латиница, цифры, _ и -")
        return v

    @field_validator("role")
    @classmethod
    def role_ok(cls, v: str) -> str:
        if v not in ("admin", "participant"):
            raise ValueError("Роль: admin или participant")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    team_id: int | None
    is_active: bool
    created_at: datetime
    university: str | None = None
    course: str | None = None
    study_program: str | None = None
    contact_extra: str | None = None

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)

    @field_validator("name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        return _clean_text(v, "Название команды")


class TeamInviteCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class TeamMemberOut(BaseModel):
    id: int
    username: str
    display_name: str
    is_owner: bool
    university: str | None = None
    course: str | None = None


class TeamInviteOut(BaseModel):
    id: int
    team_id: int
    team_name: str
    inviter_username: str
    invitee_username: str
    status: str
    created_at: datetime


class TeamOut(BaseModel):
    id: int
    name: str
    owner_id: int
    members: list[TeamMemberOut]
    pending_invites: list[TeamInviteOut]
    created_at: datetime


class RubricItem(BaseModel):
    id: str
    title: str
    max_points: float = Field(ge=0, le=100)
    description: str = ""


class RubricScoreItem(BaseModel):
    id: str
    title: str
    max_points: float
    score: float = Field(ge=0)
    description: str = ""


class EventContentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    description_md: str | None = Field(default=None, max_length=100_000)
    challenge_md: str | None = Field(default=None, max_length=100_000)
    rubric: list[RubricItem] | None = None
    ends_at: datetime | None = None
    clear_ends_at: bool = False


class EventContentOut(BaseModel):
    title: str
    description_md: str
    challenge_md: str
    has_source: bool
    source_filename: str | None
    rubric: list[RubricItem]
    ends_at: datetime | None
    seconds_left: int | None
    is_finished: bool
    updated_at: datetime | None


class ReportNoteUpdate(BaseModel):
    note: str | None = None


class ReportScoreUpdate(BaseModel):
    rubric_scores: list[RubricScoreItem]
    comment: str | None = None
    publish: bool = False

    @field_validator("rubric_scores")
    @classmethod
    def scores_ok(cls, items: list[RubricScoreItem]) -> list[RubricScoreItem]:
        for item in items:
            if item.score > item.max_points:
                raise ValueError(
                    f"Балл по «{item.title}» не может превышать {item.max_points}"
                )
        total = sum(i.score for i in items)
        if total > 100:
            raise ValueError("Сумма баллов не может превышать 100")
        return items


class ReportOut(BaseModel):
    id: int
    team_id: int
    team_name: str
    original_filename: str
    note: str | None
    submitted_by: str
    submitted_at: datetime
    updated_at: datetime
    judge_id: int | None
    judge_username: str | None
    rubric_scores: list[RubricScoreItem]
    total_score: float | None
    comment: str | None
    is_published: bool
    scored_at: datetime | None
    published_at: datetime | None
    can_view_score: bool


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

    @field_validator("body")
    @classmethod
    def body_ok(cls, v: str) -> str:
        v = v.replace("\x00", "").strip()
        if not v:
            raise ValueError("Сообщение пустое")
        return v[:5000]


class MessageOut(BaseModel):
    id: int
    author_id: int
    author_username: str
    author_role: str
    body: str
    created_at: datetime


class TicketOut(BaseModel):
    id: int
    team_id: int
    team_name: str
    status: str
    messages: list[MessageOut]
    updated_at: datetime


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
