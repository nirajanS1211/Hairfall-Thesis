#!/bin/zsh
# Hairfall Lab - start Postgres, MinIO and the app, then open the browser.
#   ./start.sh            start whatever is not running yet (a running app is left alone)
#   ./start.sh --restart  restart the app server too (refused while a step is running)
set -u
cd "$(dirname "$0")/backend"
export PATH="$HOME/.orbstack/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
URL="http://127.0.0.1:8000"
RESTART=0; [[ "${1:-}" == "--restart" ]] && RESTART=1

fail() { print -P "%F{red}✗ $1%f"; exit 1; }
ok()   { print -P "%F{green}✓%f $1"; }
wait_for() {  # wait_for <seconds> <description> <command...>
  local secs=$1 what=$2; shift 2
  for _ in $(seq 1 $secs); do "$@" >/dev/null 2>&1 && return 0; sleep 1; done
  fail "$what did not start within ${secs}s"
}

# ---- checks ----
[[ -x .venv/bin/uvicorn ]] || fail "Python environment missing - see README (python3.12 -m venv .venv && pip install -r requirements.txt)"
command -v docker >/dev/null || fail "Docker not found - install OrbStack (brew install --cask orbstack)"
command -v minio  >/dev/null || fail "MinIO not found - brew install minio"
[[ -f ../thesis_project/data/data.csv ]] || print -P "%F{yellow}!%f thesis_project/data/data.csv is missing - the Dataset tab will be empty"
[[ -f .env ]] || print -P "%F{yellow}!%f backend/.env is missing - TabPFN needs TABPFN_TOKEN (see .env.example)"
mkdir -p data/minio

# ---- Docker + Postgres ----
if ! docker info >/dev/null 2>&1; then
  open -ga OrbStack 2>/dev/null
  wait_for 90 "Docker (OrbStack)" docker info
fi
ok "Docker"
docker compose up -d >/dev/null 2>&1 || fail "docker compose up failed - run 'docker compose up' in backend/ to see why"
wait_for 60 "Postgres" docker compose exec -T postgres pg_isready -U lab
ok "Postgres"

# ---- MinIO ----
if ! pgrep -x minio >/dev/null; then
  MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
    nohup minio server data/minio --address 127.0.0.1:9000 --console-address 127.0.0.1:9001 >> data/minio.log 2>&1 &
fi
wait_for 30 "MinIO" curl -sf 127.0.0.1:9000/minio/health/live
ok "MinIO"

# ---- app ----
if curl -sf "$URL/api/status" >/dev/null; then
  if (( RESTART )); then
    curl -s "$URL/api/status" | grep -q '"running":null' || fail "A step is running - wait for it (or stop it in the Notebook) before restarting"
    pkill -TERM -f "uvicorn app.main:app"
    for _ in $(seq 1 15); do pgrep -f "uvicorn app.main:app" >/dev/null || break; sleep 1; done
  else
    ok "App already running"
  fi
fi
if ! curl -sf "$URL/api/status" >/dev/null; then
  # caffeinate keeps the Mac awake while the server runs (long training)
  nohup caffeinate -i .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 >> data/api.log 2>&1 &
  wait_for 60 "The app" curl -sf "$URL/api/status"
  ok "App"
fi

echo ""
echo "  Hairfall Lab:   $URL"
echo "  MinIO console:  http://127.0.0.1:9001  (minioadmin / minioadmin)"
echo "  Server log:     tail -f backend/data/api.log"
echo "  Stop:           ./stop.sh      Backup: ./backup.sh"
open "$URL"
