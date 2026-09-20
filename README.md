# AppSec CTF — безопасно и доступно по IP

## Модель доступа

| Порт | Снаружи? | Назначение |
|------|----------|------------|
| **3000** | да | UI + `/api` через Next.js proxy |
| **80 / 443** | да | Caddy (то же самое) |
| **8000** | **нет** | API только внутри Docker |

С другой машины: `http://IP_СЕРВЕРА:3000`

## Первый деплой

```bash
# чистый старт (если меняли схему секретов)
docker compose down
docker volume rm appsec_ctf_secrets_data appsec_ctf_postgres_data

docker compose up --build -d
docker compose logs init-secrets
```

Логин админа: **`admin-ussc`**  
Пароль: из логов `init-secrets` (или `docker compose exec api cat /secrets/CREDENTIALS.txt`)

## Что защищено

- Случайные SECRET_KEY / пароль БД / пароль админа
- API не торчит в сеть
- HttpOnly cookie + Bearer fallback, TTL 8 часов
- Rate limit на login/register
- Контейнер API не от root
- Caddy принимает запросы по IP (не только localhost)
- Авторизация отчётов/команд/чата

## Сеть

Нужен IP из `hostname -I` (например `10.129.0.26`), не `172.x` Docker.  
С интернета — публичный IP + security group на TCP 3000 (и 80 при необходимости).
