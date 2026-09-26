#!/bin/zsh
# Hairfall Lab - back up everything that is not in git: the Postgres database (runs, predictions,
# dataset) and the MinIO files (outputs, figures, records). Safe to run while the app is running.
#   ./backup.sh                 -> backups/<date-time>/
# Restore:
#   docker compose -f backend/docker-compose.yml exec -T postgres pg_restore -U lab -d lab --clean < backups/<dir>/postgres.dump
#   ./stop.sh && tar -xzf backups/<dir>/minio.tar.gz -C backend/data && ./start.sh
set -eu
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.orbstack/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
DEST="$ROOT/backups/$(date +%Y-%m-%d_%H%M%S)"
mkdir -p "$DEST"
cd "$ROOT/backend"

docker compose exec -T postgres pg_dump -U lab -d lab -Fc > "$DEST/postgres.dump"
echo "✓ Postgres  -> $DEST/postgres.dump ($(du -h "$DEST/postgres.dump" | cut -f1))"
tar -czf "$DEST/minio.tar.gz" -C data minio
echo "✓ MinIO     -> $DEST/minio.tar.gz ($(du -h "$DEST/minio.tar.gz" | cut -f1))"
[[ -f .env ]] && cp .env "$DEST/env.backup" && chmod 600 "$DEST/env.backup" && echo "✓ .env      -> $DEST/env.backup"
