#!/bin/zsh
# Hairfall Lab - start everything (Docker/Postgres, MinIO, API + UI) and open the browser.
# Usage: ./start.sh        Stop: ./stop.sh
cd "$(dirname "$0")/backend"
export PATH="$HOME/.orbstack/bin:/opt/homebrew/bin:$PATH"
URL="http://127.0.0.1:8000"

echo "1/4  Docker (OrbStack)…"
open -ga OrbStack
until docker info >/dev/null 2>&1; do sleep 2; done

echo "2/4  Postgres…"
docker compose up -d >/dev/null 2>&1
until docker compose exec -T postgres pg_isready -U lab >/dev/null 2>&1; do sleep 1; done

echo "3/4  MinIO…"
mkdir -p data/minio
if ! pgrep -x minio >/dev/null; then
  MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
    nohup minio server data/minio --address 127.0.0.1:9000 --console-address 127.0.0.1:9001 > data/minio.log 2>&1 &
fi
until curl -sf 127.0.0.1:9000/minio/health/live >/dev/null; do sleep 1; done

echo "4/4  API + UI…"
pkill -f "uvicorn app.main:app" 2>/dev/null && sleep 1
# caffeinate keeps the Mac awake while the server runs (long training)
nohup caffeinate -i .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > data/api.log 2>&1 &
until curl -sf "$URL/api/status" >/dev/null; do sleep 1; done

echo ""
echo "  Hairfall Lab is running:  $URL"
echo "  MinIO console:            http://127.0.0.1:9001  (minioadmin / minioadmin)"
echo "  Server log:               tail -f backend/data/api.log"
echo "  Stop everything:          ./stop.sh"
open "$URL"
