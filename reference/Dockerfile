# =============================================================================
# Dockerfile multi-stage — Scraper Selenium MercadoLibre — SIP 2026
#
# Uso:
#   docker build --target hit1 -t ml-scraper:hit1 .
#   docker build --target hit5 -t ml-scraper:hit5 .   (default: hit5)
#
# Variables de entorno soportadas:
#   BROWSER    chrome|firefox  (default: chrome)
#   HEADLESS   true|false      (default: true)
#   LOG_LEVEL  INFO|DEBUG|...  (default: INFO)
# =============================================================================

# =============================================================================
# Stage base: Python 3.13-slim + Chromium + Firefox + usuario non-root
# =============================================================================
FROM python:3.13-slim AS base

# Metadatos de la imagen
LABEL maintainer="SIP 2026" \
      description="Scraper Selenium MercadoLibre — imagen base" \
      org.opencontainers.image.source="https://github.com/sip2026/reference"

# Variables de entorno con defaults seguros
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BROWSER=chrome \
    HEADLESS=true \
    LOG_LEVEL=INFO \
    # Chromium necesita estas flags en contenedor sin GPU
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu" \
    # Evita que webdriver-manager intente descargar drivers (usamos los del sistema)
    WDM_LOG_LEVEL=0

# Instalar dependencias del sistema:
#   - chromium + chromium-driver: Chrome headless + chromedriver del sistema
#   - firefox-esr: Firefox headless
#   - fonts-liberation + fontconfig: fuentes para renderizado correcto en headless
#   - ca-certificates: TLS para que Selenium hable con sitios HTTPS
#   Limpiamos cache de apt en la misma capa para reducir tamaño de imagen
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        firefox-esr \
        fonts-liberation \
        fontconfig \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Crear usuario non-root "scraper" con uid 1000
# Se usa addgroup + adduser para compatibilidad con Debian/Ubuntu slim
RUN groupadd --gid 1000 scraper \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/bash scraper

# Crear directorios de trabajo con permisos para el usuario scraper
# /app         → código de la aplicación
# /app/output  → JSONs de resultados
# /app/screenshots → capturas de pantalla
# /app/logs    → logs rotativos
RUN mkdir -p /app/output /app/screenshots /app/logs \
    && chown -R scraper:scraper /app

WORKDIR /app

# Copiar requirements e instalar dependencias Python
# Esta capa se cachea mientras requirements.txt no cambie
COPY --chown=scraper:scraper requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Declarar volúmenes esperados (Docker los crea automáticamente si no se montan)
VOLUME ["/app/output", "/app/screenshots", "/app/logs"]

# Healthcheck: verifica que selenium importa correctamente
# Se ejecuta cada 30s; si falla 3 veces consecutivas, el container se marca unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import selenium; from selenium import webdriver" || exit 1

# Ejecutar como usuario non-root por defecto
USER scraper

# =============================================================================
# Stage hit1: scraper básico Chrome hardcodeado
# =============================================================================
FROM base AS hit1

WORKDIR /app/hit1

# Copiar solo los archivos del hit1 (ningún módulo extra)
COPY --chown=scraper:scraper hit1/ .

ENTRYPOINT ["python", "main.py"]

# =============================================================================
# Stage hit2: browser factory + soporte Chrome/Firefox por env/CLI
# =============================================================================
FROM base AS hit2

WORKDIR /app/hit2

# Hit2 tiene su propio browser_factory.py
COPY --chown=scraper:scraper hit2/ .

ENTRYPOINT ["python", "main.py"]

# =============================================================================
# Stage hit3: filtros DOM + screenshot
# Hit3 importa browser_factory desde hit2/ via sys.path.insert
# Por eso copiamos ambos hits al filesystem de la imagen
# =============================================================================
FROM base AS hit3

# Crear estructura de directorios que el código espera via sys.path
RUN mkdir -p /app/hit2 /app/hit3

WORKDIR /app/hit3

COPY --chown=scraper:scraper hit2/ /app/hit2/
COPY --chown=scraper:scraper hit3/ /app/hit3/

ENTRYPOINT ["python", "main.py"]

# =============================================================================
# Stage hit4: extracción estructurada JSON — 3 productos, 10 resultados c/u
# Hit4 importa browser_factory desde hit2/ via sys.path.insert
# =============================================================================
FROM base AS hit4

RUN mkdir -p /app/hit2 /app/hit4

WORKDIR /app/hit4

COPY --chown=scraper:scraper hit2/ /app/hit2/
COPY --chown=scraper:scraper hit4/ /app/hit4/

ENTRYPOINT ["python", "main.py"]

# =============================================================================
# Stage hit5: robustez — retries con backoff, ml_selectors centralizado,
#             logging rotativo
# Hit5 es self-contained: tiene su propio browser_factory, extractors, filters,
# ml_selectors y retry. No depende de hits anteriores.
# Este es el target DEFAULT cuando se construye sin --target.
# =============================================================================
FROM base AS hit5

WORKDIR /app/hit5

# Copiar hit5 completo (incluye ml_selectors.py, retry.py, etc.)
COPY --chown=scraper:scraper hit5/ .

ENTRYPOINT ["python", "main.py"]
