#!/usr/bin/env bash
# ──────────────────────────────────────────────
# SQL Agent — Quick Start
# ──────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
pip install -r requirements.txt -q --break-system-packages

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SQL QUERY AGENT — Self-Correcting NL→SQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Set your API key (optional):"
echo "    export CHATANYWHERE_API_KEY=sk-..."
echo "    export CHATANYWHERE_API_URL=https://api.chatanywhere.tech/v1/chat/completions"
echo ""
echo "  Starting on http://localhost:5000"
echo ""

python app.py
