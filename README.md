# AppSec CTF

## Доступ (как раньше) + базовая безопасность

| Порт | Назначение |
|------|------------|
| **3000** | UI |
| **8000** | API |
| 80 / 443 | Caddy (опционально) |

Открывать: `http://ПУБЛИЧНЫЙ_IP:3000`

## Безопасность при этом

- Пароли/SECRET_KEY генерируются при первом деплое (не `admin123`)
- Rate limit на login/register
- API в Docker не от root
- Админ: `admin-ussc` (или `ADMIN_USERNAME` из `.env`)

## Деплой

```bash
docker compose down
# если меняли схему секретов:
docker volume rm appsec_ctf_secrets_data appsec_ctf_postgres_data

docker compose up --build -d
docker compose logs init-secrets
bash scripts/diagnose.sh
```

Логин/пароль админа — в логах `init-secrets` или:

```bash
docker compose exec api cat /secrets/CREDENTIALS.txt
```

## Если с публичного IP не открывается, а на сервере curl ок

Проверка **с вашего ПК**:

```powershell
curl -v http://ПУБЛИЧНЫЙ_IP:3000
curl -v http://ПУБЛИЧНЫЙ_IP:8000/api/health
```

Если timeout — блок до ВМ (другая SG, NAT, IPv6). SSH на 22 не доказывает, что 3000 открыт в той же группе.
