# AppSec CTF

Платформа для командного CTF по безопасности приложений. Совместное мероприятие **УрФУ** и **УЦСБ**.

## Возможности

- Регистрация участников, вход, роли `participant` / `admin`
- Команды до 10 человек, приглашение по логину
- Сдача и пересдача отчёта (PDF, DOCX, TXT, MD)
- Оценка 0–100 по рубрике с автокалькулятором, один судья на отчёт, публикация результата
- Описание мероприятия и задание (Markdown) + скачивание ZIP исходников
- Техподдержка (один диалог на команду) + уведомления в колокольчик
- HTTPS через Caddy, автобэкапы PostgreSQL

## Быстрый старт

```bash
cp .env.example .env
# отредактируйте пароли и SECRET_KEY

docker compose up --build -d
```

Откройте (любой вариант):

- `http://localhost:3000` — напрямую Next.js (удобно для локальной разработки)
- `http://localhost:8080` или `https://localhost:8443` — через Caddy

API: `http://localhost:8000/api/health`

Учётные данные первого админа — из `.env`:

- `ADMIN_USERNAME` (по умолчанию `admin`)
- `ADMIN_PASSWORD`

API health: `https://localhost/api/health`

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `DOMAIN` | `localhost` или ваш домен (Let's Encrypt) |
| `ACME_EMAIL` | email для Let's Encrypt |
| `POSTGRES_*` | доступ к БД |
| `SECRET_KEY` | секрет JWT |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | seed-админ |
| `BACKUP_CRON` | расписание бэкапов (UTC) |
| `BACKUP_KEEP_DAYS` | сколько дней хранить дампы |

## HTTPS

- `DOMAIN=localhost` — локальный TLS Caddy
- публичный домен + порты 80/443 — автоматический Let's Encrypt

## Бэкапы

Сервис `backup` делает дамп при старте и по cron в volume `backup_data` (`appsec_ctf_YYYYMMDD_HHMMSS.sql.gz`).

Восстановление:

```bash
gunzip -c backup.sql.gz | docker compose exec -T db psql -U appsec -d appsec_ctf
```

## Структура

```
backend/   FastAPI + SQLAlchemy + PostgreSQL
frontend/  Next.js (App Router), UI на русском
backup/    скрипт автобэкапов
Caddyfile  reverse proxy + TLS
```

## Типовой сценарий

1. Админ правит контент и загружает ZIP в `/admin/content`
2. Участники регистрируются, создают команды, приглашают по логину
3. Скачивают исходники, сдают отчёт
4. Админ-судья закрепляет отчёт, выставляет баллы по критериям, публикует
5. Команда видит оценку на `/report`

## Локальная разработка (без Docker UI)

```bash
# API
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg://appsec:appsec_secret_change_me@localhost:5432/appsec_ctf
uvicorn app.main:app --reload --port 8000

# Web
cd frontend
npm install
set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
