#!/usr/bin/env bash
# 開発用の起動スクリプト
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

[ -f .env ] || { [ -f .env.example ] && cp .env.example .env && echo ".env を作成しました（必要なら eBay キーを記入）"; }

echo "http://localhost:8000 で起動します"
exec uvicorn backend.app.main:app --reload --port 8000
