#!/usr/bin/env bash
# Build UNLu-branded HTML pages from markdown sources for SIP 2026.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

TEMPLATE="$DIR/template.html"

render() {
  local src="$1"
  local out="$2"
  local title="$3"
  local banner="${4:-}"

  echo "→ $src"
  echo "   $out"

  pandoc "$src" \
    --from=gfm+smart \
    --to=html5 \
    --standalone \
    --template="$TEMPLATE" \
    --toc \
    --toc-depth=3 \
    --highlight-style=tango \
    --metadata title="$title" \
    --metadata banner-num="$banner" \
    --metadata pagetitle="$title — UNLu DCB" \
    --output "$out"
}

# ============ Render targets ============

# --- TP 1 · Parte 1 — Selenium + MercadoLibre (Hits 1-4) ---
render "TP1.md" \
  "practica-1-parte-1.html" \
  "Práctica I · Parte 1 — Selenium + MercadoLibre" \
  "TP 1 · PARTE 1"

# --- TP 1 · Parte 2 — Robustez, Tests, Docker, CI/CD (Hits 5-8) ---
render "TP2.md" \
  "practica-1-parte-2.html" \
  "Práctica I · Parte 2 — Robustez, Tests, Docker y CI/CD" \
  "TP 1 · PARTE 2"

echo ""
echo "Done. Open with:"
echo "  xdg-open $DIR/index.html"
