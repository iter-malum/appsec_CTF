# AppSec CTF

Платформа для командного CTF по безопасности приложений. Совместное мероприятие **УрФУ** и **УЦСБ**.

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs init-secrets
```

При **первом** деплое в логах `init-secrets` будут сгенерированы пароли:

```text
Admin login:       admin-ussc
Admin password:    <случайный>
Postgres password: <случайный>
```

Позже пароль админа:

```bash
docker compose exec api cat /secrets/CREDENTIALS.txt
```

Откройте UI: **http://localhost:8080** (или https://localhost:8443).

> API и Next.js **не** публикуются наружу — только через Caddy.  
> Для отладки: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`

### Важно при обновлении со старой версии

Сбросьте volumes секретов/БД (иначе останутся старые пароли):

```bash
docker compose down
docker volume rm appsec_ctf_secrets_data appsec_ctf_postgres_data
docker compose up --build -d
```

## Безопасность (встроено)

- Случайные `SECRET_KEY`, пароль БД и пароль `admin-ussc` при первом старте
- JWT в **HttpOnly** cookie (TTL 8 часов), не в `localStorage`
- Rate limit на login/register
- CORS только с разрешённых origin
- API/web не exposed наружу
- Контейнеры не от root (API через `gosu app`)
- Проверка magic bytes загрузок
- Рубрика оценки валидируется на сервере
- Security headers в Caddy

## Переменные `.env`

| Переменная | Назначение |
|---|---|
| `ADMIN_USERNAME` | Первый админ (по умолчанию `admin-ussc`) |
| `DOMAIN` | `localhost` или ваш домен |
| `COOKIE_SECURE` | `true` за публичным HTTPS |
| `CORS_ORIGINS` | Список origin через запятую |
| `HTTP_PORT` / `HTTPS_PORT` | Порты Caddy (8080 / 8443) |

Секреты (`SECRET_KEY`, пароли) **не** задаются вручную — живут в volume `secrets_data`.

## Бэкапы

```bash
gunzip -c backup.sql.gz | docker compose exec -T db psql -U appsec -d appsec_ctf
```
