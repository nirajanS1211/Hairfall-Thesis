#!/bin/zsh
# Hairfall Lab - stop API, MinIO and Postgres. All saved data is kept.
cd "$(dirname "$0")/backend"
export PATH="$HOME/.orbstack/bin:$PATH"
pkill -f "uvicorn app.main:app" && echo "API stopped"
pkill -x minio && echo "MinIO stopped"
docker compose stop >/dev/null 2>&1 && echo "Postgres stopped"
