#!/bin/sh
# Быстрая диагностика на сервере
set -eu
echo "=== compose ps ==="
docker compose ps
echo ""
echo "=== ports ==="
ss -tlnp | grep -E ':3000|:8000|:80 ' || true
echo ""
echo "=== local web ==="
curl -sI --connect-timeout 3 http://127.0.0.1:3000 | head -3 || echo FAIL_WEB
echo ""
echo "=== local api ==="
curl -s --connect-timeout 3 http://127.0.0.1:8000/api/health || echo FAIL_API
echo ""
echo "=== via next proxy ==="
curl -s --connect-timeout 3 http://127.0.0.1:3000/api/health || echo FAIL_PROXY
echo ""
IP=$(hostname -I | awk '{print $1}')
echo "=== private IP $IP ==="
curl -sI --connect-timeout 3 "http://$IP:3000" | head -3 || echo FAIL_PRIV
echo ""
echo "=== credentials ==="
docker compose exec -T api cat /secrets/CREDENTIALS.txt 2>/dev/null || echo "(no credentials file yet)"
echo ""
echo "Open in browser: http://<PUBLIC_IP>:3000"
echo "Admin password: see CREDENTIALS.txt above"
