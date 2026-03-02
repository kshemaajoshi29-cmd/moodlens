#!/usr/bin/env bash
set -euo pipefail

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[moodlens]${RESET} $*"; }
success() { echo -e "${GREEN}[moodlens]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[moodlens]${RESET} $*"; }
die()     { echo -e "${RED}[moodlens] ERROR:${RESET} $*" >&2; exit 1; }

# ── banner ───────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo "  ╔╦╗╔═╗╔═╗╔╦╗╦  ╔═╗╔╗╔╔═╗"
echo "  ║║║║ ║║ ║ ║║║  ║╣ ║║║╚═╗"
echo "  ╩ ╩╚═╝╚═╝═╩╝╩═╝╚═╝╝╚╝╚═╝"
echo -e "${RESET}  AI-powered photo mood enhancement\n"

# ── resolve project root (works when called from any directory) ───────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── optional flags ────────────────────────────────────────────────────────────
HOST="${HOST:-192.168.193.233}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"            # set RELOAD=0 to disable hot-reload (production)
WORKERS="${WORKERS:-1}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)     HOST="$2";    shift 2 ;;
    --port)     PORT="$2";    shift 2 ;;
    --no-reload) RELOAD=0;    shift   ;;
    --workers)  WORKERS="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: ./start.sh [--host HOST] [--port PORT] [--no-reload] [--workers N]"
      echo ""
      echo "  --host        Bind address (default: 0.0.0.0)"
      echo "  --port        Port to listen on (default: 8000)"
      echo "  --no-reload   Disable hot-reload (for production)"
      echo "  --workers N   Number of worker processes (disables reload)"
      exit 0 ;;
    *) die "Unknown argument: $1. Run ./start.sh --help for usage." ;;
  esac
done

# ── .env setup ────────────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
  warn ".env not found — creating from .env.example"
  cp .env.example .env
  echo ""
  echo -e "  ${YELLOW}Open ${BOLD}.env${RESET}${YELLOW} and set your API keys before continuing:${RESET}"
  echo ""
  echo "    ANTHROPIC_API_KEY=sk-ant-..."
  echo "    REPLICATE_API_TOKEN=r8_..."
  echo ""
  read -r -p "  Press Enter once you've saved your keys (Ctrl-C to abort) …"
  echo ""
fi

# ── validate required env vars ────────────────────────────────────────────────
source .env 2>/dev/null || true   # load into current shell for validation

MISSING=()
[[ -z "${OPENROUTER_API_KEY:-}" ]] && MISSING+=("OPENROUTER_API_KEY")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  die "Missing required keys in .env: ${MISSING[*]}\n  Edit .env and run again."
fi

# Quick sanity-check key prefix (doesn't call any API)
if [[ "${OPENROUTER_API_KEY}" != sk-or-* ]]; then
  warn "OPENROUTER_API_KEY doesn't look right (expected sk-or-…). Continuing anyway."
fi

# ── Python / dependency check ─────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python || true)
[[ -z "$PYTHON" ]] && die "python3 not found. Install Python 3.11+."

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 10 ]]; }; then
  die "Python 3.10+ required (found $PY_VER)."
fi

info "Python $PY_VER detected"

# Check if moodlens package is importable
if ! "$PYTHON" -c "import moodlens" 2>/dev/null; then
  info "Installing dependencies …"
  "$PYTHON" -m pip install -r requirements.txt -q
  "$PYTHON" -m pip install -e . --no-build-isolation -q
  success "Dependencies installed"
fi

# Check uvicorn specifically (needed to run the server)
if ! "$PYTHON" -m uvicorn --version &>/dev/null; then
  info "Installing uvicorn …"
  "$PYTHON" -m pip install "uvicorn[standard]" -q
fi

# ── build uvicorn command ─────────────────────────────────────────────────────
UVICORN_CMD=("$PYTHON" -m uvicorn moodlens.api.app:app --host "$HOST" --port "$PORT")

if [[ "$WORKERS" -gt 1 ]]; then
  UVICORN_CMD+=(--workers "$WORKERS")
  RELOAD=0   # multiple workers are incompatible with --reload
fi

[[ "$RELOAD" -eq 1 ]] && UVICORN_CMD+=(--reload)

# ── print startup summary ────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Endpoints${RESET}"
echo -e "    API   →  ${CYAN}http://localhost:${PORT}/api/v1/enhance${RESET}"
echo -e "    Docs  →  ${CYAN}http://localhost:${PORT}/docs${RESET}"
echo -e "    Health→  ${CYAN}http://localhost:${PORT}/health${RESET}"
echo ""
echo -e "  ${BOLD}Quick test (once running):${RESET}"
echo -e "    ${GREEN}moodlens list-presets${RESET}"
echo -e "    ${GREEN}moodlens enhance photo.jpg --mood vintage${RESET}"
echo ""
[[ "$RELOAD" -eq 1 ]] && echo -e "  ${YELLOW}Hot-reload enabled (dev mode). Use --no-reload for production.${RESET}\n"

success "Starting server on ${HOST}:${PORT} …"
echo ""

# ── launch ────────────────────────────────────────────────────────────────────
exec "${UVICORN_CMD[@]}"
