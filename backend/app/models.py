import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    participant = "participant"
    admin = "admin"


class InviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class TicketStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.participant)
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", use_alter=True, name="fk_users_team_id"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped["Team | None"] = relationship(back_populates="members", foreign_keys=[team_id])
    owned_team: Mapped["Team | None"] = relationship(
        back_populates="owner",
        foreign_keys="Team.owner_id",
        uselist=False,
    )


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(foreign_keys=[owner_id], back_populates="owned_team")
    members: Mapped[list[User]] = relationship(
        back_populates="team",
        foreign_keys=[User.team_id],
    )
    invites: Mapped[list["TeamInvite"]] = relationship(back_populates="team")
    report: Mapped["Report | None"] = relationship(back_populates="team", uselist=False)
    ticket: Mapped["SupportTicket | None"] = relationship(back_populates="team", uselist=False)


class TeamInvite(Base):
    __tablename__ = "team_invites"
    __table_args__ = (UniqueConstraint("team_id", "invitee_id", name="uq_team_invitee"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invitee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[InviteStatus] = mapped_column(Enum(InviteStatus), default=InviteStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped[Team] = relationship(back_populates="invites")
    inviter: Mapped[User] = relationship(foreign_keys=[inviter_id])
    invitee: Mapped[User] = relationship(foreign_keys=[invitee_id])


class EventContent(Base):
    __tablename__ = "event_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    title: Mapped[str] = mapped_column(String(256), default="AppSec CTF")
    description_md: Mapped[str] = mapped_column(Text, default="")
    challenge_md: Mapped[str] = mapped_column(Text, default="")
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_stored_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rubric: Mapped[list] = mapped_column(JSONB, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Scoring
    judge_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    rubric_scores: Mapped[list] = mapped_column(JSONB, default=list)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped[Team] = relationship(back_populates="report")
    submitted_by: Mapped[User] = relationship(foreign_keys=[submitted_by_id])
    judge: Mapped[User | None] = relationship(foreign_keys=[judge_id])


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), unique=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    team: Mapped[Team] = relationship(back_populates="ticket")
    messages: Mapped[list["SupportMessage"]] = relationship(
        back_populates="ticket", order_by="SupportMessage.created_at"
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("support_tickets.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped[SupportTicket] = relationship(back_populates="messages")
    author: Mapped[User] = relationship()


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()
