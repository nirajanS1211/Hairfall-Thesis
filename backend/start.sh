#!/bin/zsh
# Start everything locally: Postgres (Docker) + MinIO (binary) + API on http://127.0.0.1:8000
cd "$(dirname "$0")"
export PATH="$HOME/.orbstack/bin:$PATH"
open -a OrbStack; until docker info >/dev/null 2>&1; do sleep 2; done
docker compose up -d
mkdir -p data/minio
pgrep -x minio >/dev/null || (MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
  nohup minio server data/minio --address 127.0.0.1:9000 --console-address 127.0.0.1:9001 > data/minio.log 2>&1 &)
# caffeinate keeps the Mac awake while the API (and any long training) runs
exec caffeinate -i .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
