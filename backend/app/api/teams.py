from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.models import InviteStatus, Team, TeamInvite, User
from app.schemas import TeamCreate, TeamInviteCreate, TeamInviteOut, TeamMemberOut, TeamOut
from app.security import get_current_user, get_user_by_username
from app.services.notifications import notify_user

router = APIRouter(prefix="/teams", tags=["teams"])
settings = get_settings()


def _team_out(team: Team) -> TeamOut:
    members = [
        TeamMemberOut(
            id=m.id,
            username=m.username,
            display_name=m.display_name,
            is_owner=m.id == team.owner_id,
        )
        for m in team.members
    ]
    pending = [
        TeamInviteOut(
            id=inv.id,
            team_id=team.id,
            team_name=team.name,
            inviter_username=inv.inviter.username,
            invitee_username=inv.invitee.username,
            status=inv.status.value,
            created_at=inv.created_at,
        )
        for inv in team.invites
        if inv.status == InviteStatus.pending
    ]
    return TeamOut(
        id=team.id,
        name=team.name,
        owner_id=team.owner_id,
        members=members,
        pending_invites=pending,
        created_at=team.created_at,
    )


def _load_team(db: Session, team_id: int) -> Team:
    team = (
        db.query(Team)
        .options(
            joinedload(Team.members),
            joinedload(Team.invites).joinedload(TeamInvite.inviter),
            joinedload(Team.invites).joinedload(TeamInvite.invitee),
        )
        .filter(Team.id == team_id)
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")
    return team


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TeamOut:
    if user.team_id:
        raise HTTPException(status_code=400, detail="Вы уже состоите в команде")

    name = payload.name.strip()
    if db.query(Team).filter(Team.name == name).first():
        raise HTTPException(status_code=400, detail="Название команды уже занято")

    team = Team(name=name, owner_id=user.id)
    db.add(team)
    db.flush()
    user.team_id = team.id
    db.commit()
    return _team_out(_load_team(db, team.id))


@router.get("/mine", response_model=TeamOut | None)
def my_team(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TeamOut | None:
    if not user.team_id:
        return None
    return _team_out(_load_team(db, user.team_id))


@router.post("/{team_id}/invites", response_model=TeamInviteOut, status_code=status.HTTP_201_CREATED)
def invite_member(
    team_id: int,
    payload: TeamInviteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamInviteOut:
    team = _load_team(db, team_id)
    if user.id != team.owner_id and user.team_id != team.id:
        raise HTTPException(status_code=403, detail="Только участник команды может приглашать")
    # Prefer owner for invites, but allow any member as requested "код приглашения по логину"
    if len(team.members) >= settings.team_max_size:
        raise HTTPException(status_code=400, detail=f"Максимум {settings.team_max_size} участников")

    invitee = get_user_by_username(db, payload.username.strip().lower())
    if not invitee:
        raise HTTPException(status_code=404, detail="Пользователь с таким логином не найден")
    if invitee.role.value == "admin":
        raise HTTPException(status_code=400, detail="Администраторов нельзя приглашать в команду")
    if invitee.team_id:
        raise HTTPException(status_code=400, detail="Пользователь уже в команде")
    if invitee.id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя пригласить себя")

    existing = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.team_id == team.id,
            TeamInvite.invitee_id == invitee.id,
            TeamInvite.status == InviteStatus.pending,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Приглашение уже отправлено")

    invite = TeamInvite(
        team_id=team.id,
        inviter_id=user.id,
        invitee_id=invitee.id,
        status=InviteStatus.pending,
    )
    db.add(invite)
    notify_user(
        db,
        invitee.id,
        "Приглашение в команду",
        f"Вас пригласили в команду «{team.name}»",
        link="/team",
    )
    db.commit()
    db.refresh(invite)
    invite = (
        db.query(TeamInvite)
        .options(joinedload(TeamInvite.inviter), joinedload(TeamInvite.invitee), joinedload(TeamInvite.team))
        .filter(TeamInvite.id == invite.id)
        .first()
    )
    return TeamInviteOut(
        id=invite.id,
        team_id=team.id,
        team_name=team.name,
        inviter_username=invite.inviter.username,
        invitee_username=invite.invitee.username,
        status=invite.status.value,
        created_at=invite.created_at,
    )


@router.get("/invites/incoming", response_model=list[TeamInviteOut])
def incoming_invites(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TeamInviteOut]:
    invites = (
        db.query(TeamInvite)
        .options(
            joinedload(TeamInvite.inviter),
            joinedload(TeamInvite.invitee),
            joinedload(TeamInvite.team),
        )
        .filter(TeamInvite.invitee_id == user.id, TeamInvite.status == InviteStatus.pending)
        .all()
    )
    return [
        TeamInviteOut(
            id=i.id,
            team_id=i.team_id,
            team_name=i.team.name,
            inviter_username=i.inviter.username,
            invitee_username=i.invitee.username,
            status=i.status.value,
            created_at=i.created_at,
        )
        for i in invites
    ]


@router.post("/invites/{invite_id}/accept", response_model=TeamOut)
def accept_invite(
    invite_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamOut:
    invite = (
        db.query(TeamInvite)
        .options(joinedload(TeamInvite.team).joinedload(Team.members))
        .filter(TeamInvite.id == invite_id)
        .first()
    )
    if not invite or invite.invitee_id != user.id:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    if invite.status != InviteStatus.pending:
        raise HTTPException(status_code=400, detail="Приглашение уже обработано")
    if user.team_id:
        raise HTTPException(status_code=400, detail="Вы уже состоите в команде")

    team = invite.team
    if len(team.members) >= settings.team_max_size:
        raise HTTPException(status_code=400, detail="В команде больше нет мест")

    invite.status = InviteStatus.accepted
    user.team_id = team.id
    notify_user(
        db,
        team.owner_id,
        "Новый участник",
        f"{user.username} вступил в команду «{team.name}»",
        link="/team",
    )
    db.commit()
    return _team_out(_load_team(db, team.id))


@router.post("/invites/{invite_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_invite(
    invite_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id).first()
    if not invite or invite.invitee_id != user.id:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    if invite.status != InviteStatus.pending:
        raise HTTPException(status_code=400, detail="Приглашение уже обработано")
    invite.status = InviteStatus.declined
    db.commit()


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not user.team_id:
        raise HTTPException(status_code=400, detail="Вы не в команде")

    team = _load_team(db, user.team_id)
    if user.id == team.owner_id:
        if len(team.members) > 1:
            raise HTTPException(
                status_code=400,
                detail="Владелец не может выйти, пока в команде есть другие участники",
            )
        for inv in team.invites:
            if inv.status == InviteStatus.pending:
                inv.status = InviteStatus.cancelled
        user.team_id = None
        db.delete(team)
        db.commit()
        return

    user.team_id = None
    db.commit()


@router.post("/{team_id}/members/{member_id}/remove", response_model=TeamOut)
def remove_member(
    team_id: int,
    member_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamOut:
    team = _load_team(db, team_id)
    if user.id != team.owner_id:
        raise HTTPException(status_code=403, detail="Только владелец может исключать участников")
    if member_id == team.owner_id:
        raise HTTPException(status_code=400, detail="Нельзя исключить владельца команды")

    member = db.query(User).filter(User.id == member_id, User.team_id == team.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Участник не найден в команде")

    member.team_id = None
    notify_user(
        db,
        member.id,
        "Исключение из команды",
        f"Вас исключили из команды «{team.name}»",
        link="/team",
    )
    db.commit()
    return _team_out(_load_team(db, team.id))
