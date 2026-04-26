# Hit #7 — Dockerfile multi-stage + docker-compose + CI/CD

Empaquetado del scraper como imagen Docker (multi-stage por hit), orquestación con `docker-compose`, y pipeline de CI con matriz Chrome/Firefox + gate de cobertura + pre-commit hooks.

## Artefactos

| Archivo | Qué hace |
|---------|----------|
| [`../Dockerfile`](../Dockerfile) | Multi-stage. Targets: `base` + `hit1`, `hit2`, `hit3`, `hit4`, `hit5`. Default: `hit5` |
| [`../docker-compose.yml`](../docker-compose.yml) | 5 servicios (uno por hit) + `dev` (mount local para hot reload) + `lint` (ruff check) |
| [`../.dockerignore`](../.dockerignore) | Excluye `.git/`, `__pycache__/`, `output/`, `logs/`, `.venv/`, etc. |
| [`../.github/workflows/scrape.yml`](../.github/workflows/scrape.yml) | Pipeline GitHub Actions con matriz + gitleaks + coverage + dry-run k8s |
| [`../.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Hooks locales: gitleaks + ruff + checks varios |

## Construcción de imágenes

```bash
# Imagen del Hit 5 (default)
docker build -t ml-scraper:hit5 .

# Imagen de un hit específico
docker build --target hit3 -t ml-scraper:hit3 .

# Todas a la vez via compose
docker compose build
```

### Tamaños de imagen (referencia última corrida)

| Tag | Size |
|-----|-----:|
| `ml-scraper:hit1` | 1.62 GB |
| `ml-scraper:hit5` | 1.62 GB |

> **Nota**: el peso lo dominan Chromium (~250 MB) + Firefox (~130 MB) + sus drivers + fonts. Bajar de 1 GB requiere usar **una sola imagen por browser** (variantes `hit5-chrome` y `hit5-firefox` con un solo motor cada una), o usar imágenes oficiales `selenium/standalone-chrome` que vienen pre-armadas. Para Parte 2 dejamos la imagen "todo en uno" porque simplifica el deploy en k3s (Hit #8) — un solo `imagePullPolicy: IfNotPresent`, una sola línea de import en el cluster.

## Ejecución con Docker

```bash
# Hit 5 directo
docker run --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/screenshots:/app/screenshots \
  -e BROWSER=chrome \
  -e HEADLESS=true \
  ml-scraper:hit5

# Sobreescribir productos por CLI
docker run --rm -v $(pwd)/output:/app/output ml-scraper:hit5 \
  --browser firefox --products "iPhone 16 Pro Max" --limit 5
```

## Ejecución con docker-compose

```bash
# Levantar el Hit 5 (default service)
docker compose up hit5

# Cualquier otro hit
docker compose up hit3

# Modo dev: monta el código local, no rebuild en cada cambio
docker compose run --rm dev python hit3/main.py

# Lint
docker compose run --rm lint
```

## Pre-commit hooks (corren ANTES de cada commit local)

[`.pre-commit-config.yaml`](../.pre-commit-config.yaml) configura:

| Hook | Qué bloquea |
|------|-------------|
| `gitleaks` | Secrets hardcodeados (API keys, tokens, claves) |
| `ruff` | Errores de lint Python |
| `ruff-format` | Código mal formateado |
| `trailing-whitespace` | Espacios al final de línea |
| `end-of-file-fixer` | Archivos sin newline final |
| `check-yaml` | YAML malformado |
| `check-added-large-files` | Archivos > 500 KB (evita commitear binarios pesados por error) |

Activación local (1 vez por clone):

```bash
pip install pre-commit
pre-commit install
```

A partir de ahí, cada `git commit` corre todos los hooks. Si alguno falla, el commit no se concreta.

## Pipeline de CI (`.github/workflows/scrape.yml`)

Triggers: push a `main`, PRs a `main`, `workflow_dispatch` manual.

```
┌─────────────────────────────────────────────────────┐
│                    push / PR                        │
└─────────────────────────────────────────────────────┘
              │
       ┌──────┼──────┬─────────────┐
       ▼      ▼      ▼             ▼
    ┌──────┬─────────┬──────────┬───────────┐
    │ lint │ secrets │ unit-    │ k8s-      │
    │ ruff │gitleaks │ tests    │ validate  │
    └──┬───┴────┬────┴────┬─────┴─────┬─────┘
       │        │         │           │
       └────────┴────┬────┘           │
                     ▼                │
              ┌──────────────┐        │
              │ integration- │        │
              │ tests        │        │
              │ (matrix:     │        │
              │  chrome/ff)  │        │
              └──────┬───────┘        │
                     ▼                │
              ┌──────────────┐        │
              │ artifacts    │ ◄──────┘
              │ JSON +       │
              │ screenshots +│
              │ coverage     │
              └──────────────┘
```

**Detalles por job:**
- `lint`: `ruff check` + `ruff format --check`
- `secrets`: `gitleaks-action@v2` con `fetch-depth: 0` (escanea todo el history)
- `unit-tests`: instala deps, corre `pytest` con `--cov-fail-under=70`. Sube `htmlcov/` como artifact
- `integration-tests`: matriz `[chrome, firefox]`. Construye la imagen, corre el scraper en headless con `--limit 3` (1 producto, 3 resultados — smoke test, no full scrape para no martillar ML)
- `k8s-validation`: `kubectl apply --dry-run=client` sobre los manifiestos del Hit #8

## Conexión con Hit #8 (Kubernetes)

La imagen `ml-scraper:latest` es **la misma imagen** que se importa al cluster k3s/k3d en el Hit #8. Esto significa que cualquier optimización aplicada acá (multi-stage, non-root user, healthcheck) se hereda directamente al despliegue Kubernetes.

```bash
# Build local
docker build --target hit5 -t ml-scraper:latest .

# Importar a k3d (Mac/Windows o cross-platform)
k3d image import ml-scraper:latest -c <nombre-cluster>

# Importar a k3s nativo (Linux)
docker save ml-scraper:latest -o ml-scraper.tar
sudo k3s ctr images import ml-scraper.tar

# Aplicar manifiestos del Hit 8
kubectl apply -f hit8/k8s/
```
