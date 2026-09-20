from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import SupportMessage, SupportTicket, Team, TicketStatus, User, UserRole
from app.schemas import MessageCreate, MessageOut, TicketOut
from app.security import get_current_admin, get_current_user
from app.services.notifications import notify_admins, notify_user

router = APIRouter(prefix="/support", tags=["support"])


def _msg_out(m: SupportMessage) -> MessageOut:
    return MessageOut(
        id=m.id,
        author_id=m.author_id,
        author_username=m.author.username,
        author_role=m.author.role.value,
        body=m.body,
        created_at=m.created_at,
    )


def _ticket_out(ticket: SupportTicket) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        team_id=ticket.team_id,
        team_name=ticket.team.name,
        status=ticket.status.value,
        messages=[_msg_out(m) for m in ticket.messages],
        updated_at=ticket.updated_at,
    )


def _load_ticket(db: Session, ticket_id: int) -> SupportTicket:
    ticket = (
        db.query(SupportTicket)
        .options(
            joinedload(SupportTicket.team),
            joinedload(SupportTicket.messages).joinedload(SupportMessage.author),
        )
        .filter(SupportTicket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return ticket


@router.get("/mine", response_model=TicketOut | None)
def my_ticket(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TicketOut | None:
    if not user.team_id:
        return None
    ticket = (
        db.query(SupportTicket)
        .options(
            joinedload(SupportTicket.team),
            joinedload(SupportTicket.messages).joinedload(SupportMessage.author),
        )
        .filter(SupportTicket.team_id == user.team_id)
        .first()
    )
    return _ticket_out(ticket) if ticket else None


@router.post("/mine/messages", response_model=TicketOut)
def send_message(
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketOut:
    if not user.team_id:
        raise HTTPException(status_code=400, detail="Сначала вступите в команду")

    team = db.query(Team).filter(Team.id == user.team_id).first()
    ticket = db.query(SupportTicket).filter(SupportTicket.team_id == user.team_id).first()
    if not ticket:
        ticket = SupportTicket(team_id=user.team_id, status=TicketStatus.open)
        db.add(ticket)
        db.flush()

    ticket.status = TicketStatus.open
    ticket.updated_at = datetime.now(timezone.utc)
    msg = SupportMessage(ticket_id=ticket.id, author_id=user.id, body=payload.body.strip())
    db.add(msg)
    notify_admins(
        db,
        "Сообщение в техподдержку",
        f"Команда «{team.name if team else user.team_id}»: {payload.body.strip()[:120]}",
        link="/admin/support",
        exclude_user_id=user.id,
    )
    db.commit()
    return _ticket_out(_load_ticket(db, ticket.id))


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> list[TicketOut]:
    tickets = (
        db.query(SupportTicket)
        .options(
            joinedload(SupportTicket.team),
            joinedload(SupportTicket.messages).joinedload(SupportMessage.author),
        )
        .order_by(SupportTicket.updated_at.desc())
        .all()
    )
    return [_ticket_out(t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TicketOut:
    return _ticket_out(_load_ticket(db, ticket_id))


@router.post("/tickets/{ticket_id}/messages", response_model=TicketOut)
def admin_reply(
    ticket_id: int,
    payload: MessageCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TicketOut:
    ticket = _load_ticket(db, ticket_id)
    ticket.status = TicketStatus.open
    ticket.updated_at = datetime.now(timezone.utc)
    msg = SupportMessage(ticket_id=ticket.id, author_id=admin.id, body=payload.body.strip())
    db.add(msg)
    for member in ticket.team.members:
        notify_user(
            db,
            member.id,
            "Ответ техподдержки",
            payload.body.strip()[:160],
            link="/support",
        )
    db.commit()
    return _ticket_out(_load_ticket(db, ticket_id))


@router.post("/tickets/{ticket_id}/close", response_model=TicketOut)
def close_ticket(
    ticket_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> TicketOut:
    ticket = _load_ticket(db, ticket_id)
    ticket.status = TicketStatus.closed
    db.commit()
    return _ticket_out(_load_ticket(db, ticket_id))
