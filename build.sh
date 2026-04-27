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

# --- TP 0 — Prerrequisitos: k3s ---
render "TP0.md" \
  "practica-0.html" \
  "Práctica 0 — Prerrequisitos: k3s + Kubernetes básico" \
  "TP 0"

# --- TP 1 · Parte 1 — Selenium + MercadoLibre (Hits 1-3) ---
render "TP1.md" \
  "practica-1-parte-1.html" \
  "Práctica I · Parte 1 — Selenium + MercadoLibre" \
  "TP 1 · PARTE 1"

# --- TP 1 · Parte 2 — Robustez, Tests, Docker, k3s, CI/CD (Hits 4-9) ---
render "TP2.md" \
  "practica-1-parte-2.html" \
  "Práctica I · Parte 2 — Robustez, Tests, Docker, k3s y CI/CD" \
  "TP 1 · PARTE 2"

# --- TP 2 (TP3.md) — Observabilidad: Logging centralizado con Loki + Promtail + Grafana ---
# Nota: el archivo fuente se llama TP3.md (3er documento de la cátedra), pero en el flujo
# del alumno es la 2da práctica del cuatrimestre, por eso el banner-num es "TP 2".
render "TP3.md" \
  "practica-2.html" \
  "Práctica II — Observabilidad: Logging centralizado" \
  "TP 2"

echo ""
echo "Done. Open with:"
echo "  xdg-open $DIR/index.html"
