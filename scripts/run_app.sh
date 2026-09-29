#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
export PYTHONPATH="${ROOT}/src:${PYTHONPATH:-}"
exec streamlit run app/streamlit_app.py --server.headless true "$@"
