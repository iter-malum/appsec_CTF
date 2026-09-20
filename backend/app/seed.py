from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import EventContent, User, UserRole
from app.security import get_user_by_username, hash_password

DEFAULT_DESCRIPTION = """# AppSec CTF

Совместное мероприятие **Уральского федерального университета** и **УЦСБ**.

Проверьте навыки безопасной разработки: найдите уязвимости в учебном приложении и оформите отчёт командой.
"""

DEFAULT_CHALLENGE = """# Задание

1. Скачайте исходный код учебного приложения.
2. Проведите анализ безопасности (SAST / ручной разбор / динамика — на ваш выбор).
3. Оформите отчёт (PDF, DOCX, TXT или MD) и сдайте от имени команды.

В отчёте опишите найденные уязвимости, доказательства и рекомендации по исправлению.
"""

DEFAULT_RUBRIC = [
    {
        "id": "repro",
        "title": "Воспроизводимость находок",
        "max_points": 25,
        "description": "Чёткие шаги, PoC, окружение",
    },
    {
        "id": "severity",
        "title": "Глубина анализа",
        "max_points": 25,
        "description": "Качество и полнота исследования",
    },
    {
        "id": "impact",
        "title": "Оценка влияния",
        "max_points": 25,
        "description": "Риски, сценарии атаки, приоритеты",
    },
    {
        "id": "fix",
        "title": "Рекомендации по исправлению",
        "max_points": 25,
        "description": "Практичные и корректные фиксы",
    },
]


def ensure_seed(db: Session) -> None:
    settings = get_settings()

    admin = get_user_by_username(db, settings.admin_username.lower())
    if not admin:
        admin = User(
            username=settings.admin_username.lower(),
            password_hash=hash_password(settings.admin_password),
            display_name="Администратор",
            role=UserRole.admin,
        )
        db.add(admin)

    content = db.query(EventContent).filter(EventContent.id == 1).first()
    if not content:
        content = EventContent(
            id=1,
            title="AppSec CTF",
            description_md=DEFAULT_DESCRIPTION,
            challenge_md=DEFAULT_CHALLENGE,
            rubric=DEFAULT_RUBRIC,
        )
        db.add(content)

    db.commit()
