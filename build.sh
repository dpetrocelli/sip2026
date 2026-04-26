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

# ============ Implementación de referencia (cátedra) ============

# --- Landing de la sección de referencia ---
render "reference/README.md" \
  "reference.html" \
  "Implementación de referencia — TP Selenium MercadoLibre" \
  "REF"

# --- Hits 1-8 ---
render "reference/hit1/README.md" \
  "ref-hit1.html" \
  "Implementación de referencia — Hit #1 — Setup, búsqueda y lectura de títulos" \
  "REF · HIT 1"

render "reference/hit2/README.md" \
  "ref-hit2.html" \
  "Implementación de referencia — Hit #2 — Browser Factory" \
  "REF · HIT 2"

render "reference/hit3/README.md" \
  "ref-hit3.html" \
  "Implementación de referencia — Hit #3 — Filtros DOM + Screenshot" \
  "REF · HIT 3"

render "reference/hit4/README.md" \
  "ref-hit4.html" \
  "Implementación de referencia — Hit #4 — Extracción estructurada a JSON" \
  "REF · HIT 4"

render "reference/hit5/README.md" \
  "ref-hit5.html" \
  "Implementación de referencia — Hit #5 — Robustez, retries y logging estructurado" \
  "REF · HIT 5"

render "reference/hit6/README.md" \
  "ref-hit6.html" \
  "Implementación de referencia — Hit #6 — Tests automatizados + cobertura ≥ 70 %" \
  "REF · HIT 6"

render "reference/hit7/README.md" \
  "ref-hit7.html" \
  "Implementación de referencia — Hit #7 — Dockerfile multi-stage + docker-compose + CI/CD" \
  "REF · HIT 7"

render "reference/hit8/README.md" \
  "ref-hit8.html" \
  "Implementación de referencia — Hit #8 — Despliegue en Kubernetes (k3s / k3d)" \
  "REF · HIT 8"

# --- Lecciones de la Parte 1 ---
render "reference/docs/parte-1-lecciones.md" \
  "ref-lecciones-parte1.html" \
  "Implementación de referencia — TP 1 · Parte 1 — Lecciones del curso" \
  "REF · LECCIONES"

# --- ADRs (Architecture Decision Records) ---
render "reference/docs/adr/0000-template.md" \
  "ref-adr-template.html" \
  "Implementación de referencia — ADR · Plantilla" \
  "REF · ADR"

render "reference/docs/adr/0001-selenium-vs-playwright.md" \
  "ref-adr-0001.html" \
  "Implementación de referencia — ADR 0001 — Selenium WebDriver (no Playwright/Puppeteer/Cypress)" \
  "REF · ADR 0001"

render "reference/docs/adr/0002-multi-browser-chrome-firefox.md" \
  "ref-adr-0002.html" \
  "Implementación de referencia — ADR 0002 — Soportar Chrome y Firefox desde el Hit #2" \
  "REF · ADR 0002"

render "reference/docs/adr/0003-k8s-job-vs-docker-compose.md" \
  "ref-adr-0003.html" \
  "Implementación de referencia — ADR 0003 — Kubernetes Job + CronJob (k3s/k3d) en lugar de docker-compose" \
  "REF · ADR 0003"

echo ""
echo "Done. Open with:"
echo "  xdg-open $DIR/index.html"
