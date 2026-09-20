from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def username_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Логин: только латиница, цифры, _ и -")
        return v


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
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

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)


class TeamInviteCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class TeamMemberOut(BaseModel):
    id: int
    username: str
    display_name: str
    is_owner: bool


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
    title: str | None = None
    description_md: str | None = None
    challenge_md: str | None = None
    rubric: list[RubricItem] | None = None


class EventContentOut(BaseModel):
    title: str
    description_md: str
    challenge_md: str
    has_source: bool
    source_filename: str | None
    rubric: list[RubricItem]
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
    # for participants: hide unpublished scoring
    can_view_score: bool


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


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
