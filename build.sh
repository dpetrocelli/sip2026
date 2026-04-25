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

# --- TP 1 — Automatización Web con Selenium (MercadoLibre) ---
render "TP1.md" \
  "practica-1.html" \
  "Práctica I — Automatización Web con Selenium (MercadoLibre)" \
  "TP 1"

echo ""
echo "Done. Open with:"
echo "  xdg-open $DIR/index.html"
