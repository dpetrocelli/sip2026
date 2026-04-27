# Trabajo Práctico Nº 1 — Parte 2

## Robustez, Tests, Docker, Kubernetes y CI/CD sobre el scraper de MercadoLibre

**Fecha de Entrega: 02/05/2026**

**Pre-requisitos:**
- Haber entregado la **Parte 1** (Hits #1–#3). Esta segunda parte continúa el mismo proyecto y arranca con el Hit #4 (extracción estructurada a JSON), que es la base sobre la que se construye el resto.
- Haber completado la guía del **TP 0 — Prerrequisitos (k3s)** antes de empezar el Hit #7. Sin un cluster k3s/k3d funcional no podés cumplir esa parte.

---

## Requisitos, consideraciones y formato de entrega

Aplican los mismos requisitos generales de la Parte 1, **más** los siguientes:

### Infra base obligatoria — bloqueante

> 🚧 **Sin esto no se puede evaluar la entrega.** El resto de los hits se valida **a través** de esta infra (la cátedra corre tu pipeline + tu `docker compose up` + tu Job en k8s para corregir Hits 4-8). Si la infra no funciona, no se llega a corregir nada más → **nota 0**. No suma puntos en la rúbrica porque es condición necesaria para que la entrega exista.

- **Dockerfile multi-stage obligatorio** que empaquete el scraper con Chrome + Firefox + drivers, ejecutable con un solo comando:

  ```bash
  docker run --rm -v $(pwd)/output:/app/output ml-scraper:latest --browser firefox
  ```

  Pin de versiones obligatorio (no `:latest` en bases). Esqueleto multi-stage [más abajo](#esqueleto-del-dockerfile-multi-stage-infra-base).

- **`docker-compose.yml` obligatorio** que levante el scraper con un solo comando, sin tener que recordar los flags de `docker run`. Mínimo: servicio `scraper` con `BROWSER`/`HEADLESS` parametrizables vía env y mount `./output:/app/output`. Idealmente también un servicio `lint` invocable con `docker compose run --rm lint`:

  ```bash
  docker compose up scraper          # corre los 3 productos contra el browser default
  BROWSER=firefox docker compose up scraper
  docker compose run --rm lint       # lint sin instalar nada local
  ```

- **Pipeline GitHub Actions** (`.github/workflows/scrape.yml`) que:
  1. Construya la imagen Docker.
  2. Corra el scraper headless contra **Chrome y Firefox** (jobs en paralelo, matriz).
  3. Ejecute los **tests del Hit #6** + verifique **cobertura ≥ 70 %** (el pipeline debe fallar si cae debajo del umbral, medido con `coverage.py` / `jest --coverage` / `jacoco` según stack).
  4. Publique JSON + screenshots + reporte de cobertura como **artifacts** del workflow.
  5. Falle si **gitleaks** detecta secrets hardcodeados.

- **Pre-commit hooks** locales (`.pre-commit-config.yaml` o equivalente nativo del stack) con mínimo:
  - `gitleaks` — bloquea commits con secrets.
  - Linter del lenguaje (`ruff` / `eslint` / `checkstyle`).
  - Formatter (`black` / `prettier` / `spotless`).

  Documenten en el README cómo activarlos: `pre-commit install` (Python/Node) o equivalente del stack. Esto fuerza que los problemas se detecten **antes** de pushear, no recién en CI.

### Otros requisitos

- **Mínimo 4 ADRs** (Architecture Decision Records) en `docs/adr/`, formato Markdown corto (1 página máx cada uno). Composición obligatoria:
  - **2 ADRs elegidos del menú abajo** (los que más aplican a las decisiones que efectivamente tomaron).
  - **2 ADRs de su elección** (decisiones reales del equipo que no estén en el menú — por ejemplo: lenguaje del scraper, registry público que usaron, dep manager, esquema de versionado de la imagen, política de logs, manejo de secrets, etc.).
  - **Formato**: [Michael Nygard template](https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md) (Contexto · Decisión · Consecuencias). Copien a `docs/adr/0000-template.md` como base.
  - **Más ejemplos y plantillas alternativas**: <https://github.com/joelparkerhenderson/architecture-decision-record> (la colección canónica de Nygard, con 30+ templates y 100+ ejemplos reales de empresas).

  **Menú de ADRs propuestos** (elijan 2):

  | Archivo sugerido | Decisión a documentar |
  |---|---|
  | `0001-framework-automatizacion.md` | Por qué Selenium (y no Playwright/Puppeteer/Cypress) — o al revés si eligieron otro. |
  | `0002-multi-browser.md` | Por qué soportar Chrome **y** Firefox simultáneo, en lugar de uno solo. |
  | `0003-orquestacion-batch.md` | Por qué Kubernetes Job/CronJob (y no `docker-compose` + cron del host, o un Deployment con sidecar). |
  | `0004-estrategia-selectores.md` | Por qué la estrategia de selectores que usaron (estructura semántica vs `data-*` vs XPath posicional) y cómo planean adaptarse a cambios de DOM de ML. |
  | `0005-estrategia-retries.md` | Por qué retries con backoff exponencial (y no circuit breaker, fail-fast, o sin retries). Parámetros elegidos (intentos, base delay) y por qué. |
  | `0006-pre-commit-vs-ci.md` | Qué se valida en pre-commit local vs CI remoto, y por qué la división. Trade-off de tiempo de feedback vs costo de CI. |

- Mantener las **buenas prácticas** ya exigidas en Parte 1: explicit waits, selectores en módulo aparte, logs estructurados, no commitear secrets.

---

## Contenidos del programa relacionados

- Robustez en automatización: timeouts, retries, manejo de fallos parciales.
- Headless browsing y empaquetado en contenedores.
- Testing de software: integración, contratos de datos, schemas, cobertura.
- Pipelines de CI/CD y matrices de ejecución.
- Orquestación de containers con Kubernetes: Job, CronJob, ConfigMap, PVC.
- Calidad de código: pre-commit hooks, linters, ADRs como documentación viva.
- Patrones avanzados: Page Object Model.

---

## Práctica

En la **Parte 1** construyeron un scraper multi-browser que busca productos en MercadoLibre y aplica filtros vía DOM (Hits #1–#3). En esta **Parte 2** lo llevamos a calidad de producción: empezamos por la **extracción estructurada a JSON de los 3 productos** (Hit #4), y luego sumamos robustez ante fallos, modo headless, tests automatizados, empaquetado en Docker, y pipeline de CI/CD que ejecute todo con cada push.

Continuamos con los mismos productos:

1. `Bicicleta rodado 29`
2. `iPhone 16 Pro Max`
3. `GeForce RTX 5090`

---

### Hit #4

Generalice el flujo del Hit #3 para que reciba como entrada una lista de productos (los 3 del enunciado: bicicleta rodado 29, iPhone 16 Pro Max, GeForce RTX 5090) y los procese todos.

Para cada producto, extraiga los **primeros 10 resultados** filtrados y, por cada uno, capture los siguientes campos:

- `titulo` — título del producto
- `precio` — precio en ARS (numérico, sin símbolo `$` ni separadores)
- `link` — URL completa al detalle del producto
- `tienda_oficial` — nombre de la tienda oficial (si aparece, sino `null`)
- `envio_gratis` — booleano
- `cuotas_sin_interes` — string con la oferta de cuotas (si aparece, sino `null`)

Guarde la salida en archivos separados por producto, en formato JSON:

- `output/bicicleta_rodado_29.json`
- `output/iphone_16_pro_max.json`
- `output/geforce_5090.json`

El JSON debe ser un array de objetos, uno por resultado, con los campos definidos arriba.

---

### Hit #5

Endurezca el scraper para que sea **robusto frente a fallos parciales**:

1. Si un campo opcional no aparece en un resultado (ej: producto sin cuotas), el scraper debe registrar `null` y continuar — no debe romper la ejecución.
2. Si un selector falla por timeout, registre el error en el log con contexto (qué producto, qué browser, qué selector) y continúe con el siguiente resultado.
3. Implemente un mecanismo de **reintentos con backoff** ante fallos transitorios de carga (ej: 3 intentos con 2s, 4s, 8s).
4. Estructure los selectores en un módulo aparte (constantes con nombres semánticos), de modo que un cambio de DOM en MercadoLibre se arregle en un solo lugar.

---

### Hit #6

Agregue **modo headless** controlable por variable de entorno (`HEADLESS=true`).

Escriba un set de **tests automatizados** (`pytest` / `JUnit` / `Jest`) que validen:

- Que el scraper extrae al menos 10 resultados por producto.
- Que el JSON generado cumple un schema mínimo (todos los campos requeridos, tipos correctos).
- Que los precios extraídos son números positivos.
- Que todos los links son URLs absolutas válidas.

Los tests deben correr en CI tanto en Chrome como en Firefox.

**Cobertura mínima: 70 %.** Configure el reporte de cobertura (`coverage.py` + `pytest-cov`, `jest --coverage`, `jacoco`) y agregue una etapa al pipeline de CI que **falle si la cobertura cae debajo del 70 %**. Publique el reporte HTML como artifact del workflow.

---

### Hit #7 — Despliegue en Kubernetes (k3s)

**Pre-requisito:** haber completado el [TP 0](practica-0.html) y tener un cluster k3s o k3d funcional.

Empaquete el scraper construido en la Infra base como una carga de trabajo de Kubernetes. El objetivo es ir más allá de "corre en mi máquina con Docker" y demostrar que la solución se puede desplegar en un orquestador.

#### 8.1 — `Job` one-off

Cree `k8s/job.yaml` que ejecute el scraper **una vez** contra los 3 productos en headless Chrome, escribiendo los JSON en un volumen persistente.

#### 8.2 — `CronJob` programado

Cree `k8s/cronjob.yaml` que ejecute el mismo scraping **cada hora** (`0 * * * *`), conservando un histórico en el volumen persistente.

#### 8.3 — `ConfigMap` con configuración

Externaliza `BROWSER`, `HEADLESS`, `LOG_LEVEL` y la lista de productos a buscar en un `k8s/configmap.yaml`. Tanto el `Job` como el `CronJob` deben leer su configuración desde ahí.

#### 8.4 — `PersistentVolumeClaim` para los outputs

Cree `k8s/pvc.yaml` que solicite 1 GB con la storage class `local-path` (que k3s trae out-of-the-box). Los JSON y screenshots se escriben acá.

#### Esqueleto orientativo

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scraper-config
data:
  BROWSER: "chrome"
  HEADLESS: "true"
  LOG_LEVEL: "INFO"
  PRODUCTS: |
    bicicleta rodado 29
    iPhone 16 Pro Max
    GeForce RTX 5090

---
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: scraper-output
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi

---
# k8s/job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: scraper-once
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: scraper
        image: ml-scraper:latest
        imagePullPolicy: IfNotPresent
        envFrom:
        - configMapRef:
            name: scraper-config
        volumeMounts:
        - name: output
          mountPath: /app/output
      volumes:
      - name: output
        persistentVolumeClaim:
          claimName: scraper-output

---
# k8s/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scraper-hourly
spec:
  schedule: "0 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: scraper
            image: ml-scraper:latest
            imagePullPolicy: IfNotPresent
            envFrom:
            - configMapRef:
                name: scraper-config
            volumeMounts:
            - name: output
              mountPath: /app/output
          volumes:
          - name: output
            persistentVolumeClaim:
              claimName: scraper-output
```

#### Recetario de ejecución

```bash
# 1. Construir la imagen Docker (igual que en Infra base)
docker build -t ml-scraper:latest .

# 2. Cargar la imagen en el cluster
# Si usás k3s nativo:
docker save ml-scraper:latest -o ml-scraper.tar
sudo k3s ctr images import ml-scraper.tar
rm ml-scraper.tar

# Si usás k3d:
k3d image import ml-scraper:latest -c scraper

# 3. Aplicar todos los manifiestos
kubectl apply -f k8s/

# 4. Disparar el Job one-off y seguir los logs
kubectl get jobs
kubectl logs -l job-name=scraper-once -f

# 5. Inspeccionar el PVC y verificar los JSON
kubectl get pvc
kubectl exec -it $(kubectl get pod -l job-name=scraper-once -o jsonpath='{.items[0].metadata.name}') -- ls /app/output

# 6. Verificar el CronJob
kubectl get cronjobs
kubectl get jobs --watch  # vas a ver corridas cada hora

# 7. Cleanup
kubectl delete -f k8s/
```

#### Entregables del Hit #7

- Carpeta `k8s/` con los 4 YAMLs.
- Sección en el README explicando: cómo levantar el cluster (referenciando TP 0), cómo cargar la imagen, cómo aplicar los manifiestos, cómo verificar.
- Captura de pantalla (o asciinema) de `kubectl get jobs` mostrando un Job completado y `kubectl get cronjobs` mostrando el cron activo.
- Bonus: agregar al pipeline de CI una etapa que valide la sintaxis de los YAMLs con `kubectl apply --dry-run=client -f k8s/`.

---

### Hit #8 — Capacidad extendida

Extienda el scraper con **las siguientes 3 capacidades**:

1. **Paginación**: traer los primeros 30 resultados en lugar de 10, navegando hasta 3 páginas.
2. **Comparación de precios**: para cada producto, calcular precio mínimo, máximo, mediana y desvío estándar entre los resultados extraídos. Imprimir tabla resumen.
3. **Histórico con PostgreSQL**: guardar los resultados en una instancia PostgreSQL con timestamp, para detectar cambios de precio entre corridas del CronJob (Hit #7). Implementación esperada: deployment de Postgres en el mismo cluster k3s (StatefulSet + PVC + Service), credenciales via `Secret`, schema migrations (Alembic / Flyway / Liquibase / SQL files versionados). Tabla mínima: `(producto, titulo, precio, link, tienda_oficial, scraped_at)`.

---

## Material de apoyo

### Tabla de herramientas por lenguaje

Para que no pierdan tiempo eligiendo, esto es lo que esperamos en cada stack:

| Stack | Coverage tool | Linter | Formatter | Pre-commit framework |
|-------|---------------|--------|-----------|----------------------|
| **Python 3.13** | `coverage.py` + `pytest-cov` (gate: `--cov-fail-under=70`) | `ruff check` | `ruff format` (o `black`) | `pre-commit` ([pre-commit.com](https://pre-commit.com/)) |
| **Node.js 20** | `jest --coverage` con `coverageThreshold` ≥ 70 % | `eslint` | `prettier` | `husky` + `lint-staged` o `pre-commit` |
| **Java 17** | `jacoco` (`<minimum>0.70</minimum>` en `jacoco-maven-plugin`) | `checkstyle` o `pmd` | `spotless` (google-java-format) | `pre-commit` con hooks Maven |

### Plantilla de ADR (`docs/adr/0000-template.md`)

Formato Michael Nygard, 1 página. Copien esto a `docs/adr/0000-template.md` y úsenlo como base para los **4 ADRs obligatorios** (2 del menú + 2 propios).

**Referencias:**
- [Plantilla original de Michael Nygard](https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md) — la versión que adoptamos en este TP.
- [Colección completa de Nygard](https://github.com/joelparkerhenderson/architecture-decision-record) — 30+ plantillas alternativas (MADR, Y-statement, OSSWatch, etc.) y 100+ ADRs reales de empresas para inspirarse.
- [Documenting Architecture Decisions, Michael Nygard 2011](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — el post original que inició la práctica.

```markdown
# 000X — <Título corto, en imperativo>

- **Date:** YYYY-MM-DD
- **Status:** Accepted | Proposed | Deprecated | Superseded by 000Y
- **Deciders:** <integrantes que tomaron la decisión>

## Contexto

¿Qué problema o trade-off estamos enfrentando? ¿Cuáles son las alternativas que consideramos?
2-4 párrafos cortos.

## Decisión

¿Qué decidimos hacer? Una oración clara.

## Consecuencias

- Lo que se vuelve **más fácil** con esta decisión.
- Lo que se vuelve **más difícil** o se sacrifica.
- Riesgos conocidos y cómo se mitigan.

## Referencias

- Links a docs, papers, charlas que informaron la decisión.
```

**Ejemplo concreto** de un ADR (`0001-framework-automatizacion.md`):

```markdown
# 0001 — Usamos Selenium WebDriver y no Playwright

- Date: 2026-04-15
- Status: Accepted
- Deciders: Juan Pérez, María García

## Contexto

Necesitamos automatizar un browser para scrapear MercadoLibre. Las alternativas son:
- **Selenium** (W3C standard, soporte multi-lenguaje, ecosistema enorme).
- **Playwright** (más rápido, mejor DX, soporta multi-browser nativo).
- **Puppeteer** (Chrome-only, descartado por requisito multi-browser).
- **Cypress** (E2E pero pensado para apps propias, no scraping de terceros).

## Decisión

Usamos **Selenium 4** porque la consigna del TP exige Selenium específicamente como
herramienta de aprendizaje (estándar W3C WebDriver), y porque queremos exposición a la
herramienta más usada en la industria para QA.

## Consecuencias

- Más fácil: comunidad enorme, drivers nativos para Chrome/Firefox/Edge, bindings en Python/Java/JS/Ruby/C#.
- Más difícil: API más verbosa que Playwright, no maneja contextos paralelos automáticamente, debemos manejar waits explícitos manualmente.
- Riesgo: scripts más frágiles ante cambios del DOM. Mitigamos con selectores estables (Hit #5) y reintentos con backoff.

## Referencias

- W3C WebDriver spec: https://www.w3.org/TR/webdriver2/
- Selenium docs: https://www.selenium.dev/documentation/
```

### Esqueleto del Dockerfile multi-stage (Infra base)

Esto es un punto de partida. Adapten al lenguaje. La idea es **multi-stage** para que la imagen final sea lo más chica posible (no necesitan compiladores ni headers en runtime).

> **🔒 Pin de versiones obligatorio.** Nunca usen `:latest` en una imagen base — cada `docker build` puede traer bytes distintos y rompe la reproducibilidad. Mínimo aceptable: pin a `MAJOR.MINOR-<distro>` (ej: `python:3.13-slim-trixie`). Mejor: pin a `MAJOR.MINOR.PATCH`. Production-grade: pin por digest sha256 (`@sha256:...`). En 2026 **usen las versiones LTS más nuevas**: Python 3.13, Node 24 (LTS Oct 2025), Java 25 (LTS Sept 2025).

```dockerfile
# ============ Stage 1: builder (deps + compile) ============
FROM python:3.13-slim-trixie AS builder
WORKDIR /app

# System deps para compilar wheels si hace falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============ Stage 2: runtime (browsers + app) ============
FROM python:3.13-slim-trixie AS runtime
WORKDIR /app

# Instalar Google Chrome stable + Firefox + deps mínimas
# Nota: NO uses `chromium` de Debian trixie (bug de crashpad en headless).
# Usá google-chrome-stable del repo oficial.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    firefox-esr \
    fonts-liberation \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends \
       google-chrome-stable \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copiar deps de Python desde el builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Usuario no-root con HOME (Chrome necesita ~/.local para crashpad)
RUN useradd --create-home --uid 1000 scraper
USER scraper

COPY --chown=scraper:scraper . .

# Healthcheck — opcional pero recomendado
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import selenium; print('ok')" || exit 1

ENTRYPOINT ["python", "scraper.py"]
CMD ["--browser", "chrome"]
```

**Equivalentes para otros stacks** (pinear MAJOR.MINOR + distro como mínimo, usar versiones LTS más nuevas de 2026):

- **Node 24 LTS (Active LTS desde Oct 2025)**:
  - Builder: `FROM node:24-trixie-slim AS builder` → `npm ci --omit=dev`
  - Runtime: `FROM node:24-trixie-slim AS runtime` + browsers (mismo bloque de Chrome de arriba) + `USER node`
- **Java 25 LTS (LTS desde Sept 2025)**:
  - Builder: `FROM maven:3.9-eclipse-temurin-25-noble AS builder` → `mvn -B package -DskipTests`
  - Runtime: `FROM eclipse-temurin:25-jre-noble AS runtime` + browsers + copiar `.jar` desde builder + `USER 1000`

> **⚠️ User-Agent custom obligatorio en headless.** MercadoLibre detecta Chrome/Firefox headless con UA por defecto y devuelve la página **sin resultados**. En el código del scraper (no en el Dockerfile) hay que setear:
>
> ```python
> options.add_argument(
>   '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
>   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
> )
> ```
>
> Equivalente Java: `options.addArguments("--user-agent=...")`. Equivalente JS: `options.addArguments('--user-agent=...')` o `setUserAgent()` en Puppeteer/Playwright. Sin esto, el pipeline de CI funciona pero los JSON salen vacíos.

### Esqueleto del workflow de CI (`.github/workflows/scrape.yml`, Infra base)

```yaml
name: Scraper CI

on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
    steps:
      - uses: actions/checkout@v4

      - name: Detect secrets with gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Build Docker image
        run: docker build -t ml-scraper:ci .

      - name: Run scraper (headless ${{ matrix.browser }})
        run: |
          docker run --rm \
            -e BROWSER=${{ matrix.browser }} \
            -e HEADLESS=true \
            -v ${{ github.workspace }}/output:/app/output \
            ml-scraper:ci

      - name: Run tests with coverage gate
        run: |
          docker run --rm \
            -v ${{ github.workspace }}/coverage:/app/coverage \
            ml-scraper:ci \
            pytest --cov=. --cov-report=html:/app/coverage --cov-fail-under=70

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: scraper-output-${{ matrix.browser }}
          path: |
            output/
            coverage/

  validate-k8s:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Validate Kubernetes manifests (dry-run)
        run: |
          for f in k8s/*.yaml; do
            kubectl apply --dry-run=client -f "$f"
          done
```

### Esqueleto de pre-commit (`.pre-commit-config.yaml`)

Aplica a Python como ejemplo. Para Node sustituyan los hooks de `ruff` por `eslint`/`prettier`.

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Activar local: `pip install pre-commit && pre-commit install`. Documenten el comando en el README.

---

## Cómo entregar

1. **Push final al repo público** antes del 02/05/2026 23:59 ART.
2. **README raíz actualizado** con:
   - Sección "Prerrequisitos cumplidos" mostrando evidencia del checklist del [TP 0](practica-0.html).
   - Cómo correr Parte 1 + Parte 2 (Docker, k3s/k3d).
   - Comandos exactos para reproducir el demo del Hit #7.
3. **Carpeta `docs/adr/`** con mínimo 4 ADRs (2 elegidos del menú + 2 de su elección).
4. **Video** mostrando: Hit #4 corriendo (con JSON resultante), pipeline de CI verde con coverage ≥ 70 %, `kubectl apply -f k8s/` con Job completado y CronJob activo.
5. **Mensaje en el canal Discord de la materia** con el link al repo y al video.

> 📡 **Canal Discord (consultas + entregas):** <https://discord.com/channels/1482135908508500148/1482135909456679139>
> Antes de pedir ayuda con k3s, revisá el [TP 0](practica-0.html) y la sección de troubleshooting que ya tiene los 4 errores típicos.

---

## Auto-verificación previa a la entrega

Antes de pushear el commit final, corré estos comandos en tu repo. Si **algo de esta lista falla, todavía no entregues** — vas a perder puntos seguros que se evitan con 2 minutos de checklist.

### 1) Tests + cobertura ≥ 70 %

```bash
# Python
pytest --cov=. --cov-fail-under=70

# Node
npm test -- --coverage --coverageThreshold='{"global":{"lines":70}}'

# Java
mvn verify   # con jacoco-maven-plugin configurado con minimum 0.70
```

### 2) Linter + formatter (los mismos que corren en pre-commit)

```bash
ruff check . && ruff format --check .          # Python
npx eslint . && npx prettier --check .          # Node
mvn spotless:check && mvn checkstyle:check      # Java
```

### 3) Detección de secrets

```bash
gitleaks detect --no-git --verbose
# alternativa si ya está configurado pre-commit:
pre-commit run gitleaks --all-files
```

### 4) Manifests Kubernetes válidos

```bash
for f in k8s/*.yaml; do
  kubectl apply --dry-run=client -f "$f" || echo "❌ $f rompe"
done
```

### 5) Build de la imagen Docker

```bash
docker build -t ml-scraper:test .
docker run --rm -e HEADLESS=true -e BROWSER=chrome \
  -v $(pwd)/output:/app/output \
  ml-scraper:test --limit 3
# Verificá que se generen los 3 JSON en output/
```

### 6) Comparación contra el golden master (opcional pero recomendado)

La cátedra publicó la implementación de referencia con un `tooling/compare.py` que valida estructura, schema, presencia de hits, anti-patterns y secrets. Pueden correrla contra su propio repo para tener feedback antes de entregar:

```bash
git clone https://github.com/dpetrocelli/sip2026.git /tmp/sip-ref
python /tmp/sip-ref/reference/tooling/compare.py \
  --student . --out /tmp/mi-evaluacion.md
cat /tmp/mi-evaluacion.md
```

El reporte indica qué hits encuentra, qué anti-patterns detecta (`time.sleep`, selectores hardcodeados, secrets, etc.) y un score estimado. **No reemplaza la corrección humana**, pero detecta los errores estructurales más comunes.

### 7) E2E completo en cluster local

```bash
# Cargá la imagen al cluster (k3s o k3d)
docker save ml-scraper:test -o /tmp/img.tar && sudo k3s ctr images import /tmp/img.tar
# o:  k3d image import ml-scraper:test -c <tu-cluster>

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
kubectl wait --for=condition=complete job/scraper-once --timeout=600s -n ml-scraper
kubectl logs -l job-name=scraper-once -n ml-scraper
```

Si el Job termina en `Complete` y los logs muestran los 3 JSON generados, están listos para entregar.

---

## Criterios de evaluación — Parte 2

### Requisitos bloqueantes (no se acepta la entrega sin estos)

Estos no suman puntos — son condición necesaria para que la entrega sea **corregible**. Si falta cualquiera de los 4, la nota es 0.

- **TP 0 cumplido** — checklist de prerrequisitos k3s con evidencia en el README (`kubectl get nodes` Ready, nginx-test corrió, sé importar imágenes al cluster).
- **Infra base** completa y funcional:
  - `Dockerfile` multi-stage con versiones pineadas (no `:latest`).
  - `docker-compose.yml` que levanta el scraper con un solo comando.
  - Pipeline GitHub Actions corriendo en verde con matriz Chrome/Firefox + gate de cobertura ≥ 70 % + gitleaks + artifacts publicados.
  - `.pre-commit-config.yaml` con gitleaks + linter + formatter, documentado en el README cómo activarlo.
- **Modo headless** configurable por env (`HEADLESS=true`) y operativo en CI sin abrir display gráfico.
- **Auto-verificación** ejecutada antes del push final ([checklist completo abajo](#auto-verificación-previa-a-la-entrega)) — los 7 comandos pasaron.

### Tabla de puntaje (100 %)

| Criterio | Peso |
|----------|------|
| **Hit #4** — extracción estructurada a JSON de los 3 productos con todos los campos | 25 % |
| **Hit #5** — manejo robusto de errores (selectores faltantes, timeouts, retries con backoff) | 15 % |
| **Hit #6** — tests automatizados + cobertura ≥ 70 % validada en CI | 15 % |
| **Hit #7** — `Job` + `CronJob` + `ConfigMap` + `PVC` corriendo en k3s/k3d | 20 % |
| **Hit #8** — capacidad extendida (paginación + stats + histórico PostgreSQL en k3s) | 15 % |
| **ADRs** (mínimo 4 en `docs/adr/` — 2 del menú propuesto + 2 de elección propia) | 10 % |

---

## Referencias y Bibliografía

Solo lo directamente vinculado a lo que se les pide en Parte 2. Los libros generales de Kubernetes / containers viven en el [TP 0](practica-0.html#lectura-recomendada-y-referencias) y no se repiten.

### Hit #4 — Extracción JSON estructurada

- **JSON Schema** — el estándar para validar la estructura del output. Si quieren ir un paso más, agreguen un test que valide cada `output/*.json` contra un schema. <https://json-schema.org/>
- **Python `json` stdlib / Node `JSON` global / Jackson (Java)** — APIs nativas de cada stack. Sin librerías externas alcanza para el Hit #4.

### Hit #5 — Robustez, retries y logging

- **AWS Builders' Library — Timeouts, retries and backoff with jitter** (Marc Brooker, 2019) — el artículo de referencia técnica sobre por qué backoff exponencial **necesita jitter** para no causar thundering herd. Cortito y al hueso. <https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/>
- **Google SRE Book — Cap. 22: Addressing Cascading Failures** — cuándo los retries empeoran el problema en lugar de arreglarlo. <https://sre.google/sre-book/addressing-cascading-failures/>
- **`tenacity` (Python)** — librería estándar de facto para retries con backoff (alternativa a escribir el decorador a mano). <https://tenacity.readthedocs.io/>
- **Python `logging` HOWTO** — niveles, handlers, rotación. Lo que se les pide en Hit #5 está acá. <https://docs.python.org/3/howto/logging.html>

### Hit #6 — Tests automatizados + cobertura

- **pytest documentation** — fixtures, parametrize, markers. <https://docs.pytest.org/>
- **`coverage.py`** — la lib que mide cobertura para Python (la usa `pytest-cov` por debajo). Lean la sección "Excluding code from coverage" para saber qué excluir y qué no. <https://coverage.readthedocs.io/>
- **`pytest-cov`** — plugin que integra coverage con pytest + el flag `--cov-fail-under=70` que les piden. <https://pytest-cov.readthedocs.io/>
- **Equivalentes**: [`jest --coverage`](https://jestjs.io/docs/cli#--coverageboolean) (Node) · [`jacoco-maven-plugin`](https://www.eclemma.org/jacoco/trunk/doc/maven.html) (Java)
- **Hutchins, M.; Foster, H.; Goradia, T.; Ostrand, T. (1994).** "Experiments on the Effectiveness of Dataflow- and Control-Flow-Based Test Adequacy Criteria". *ICSE 1994.* — el paper original que establece por qué la cobertura ≥ 70 % NO es la métrica completa pero sí un piso razonable. <https://dl.acm.org/doi/10.5555/257734.257766>

### Infra base — Dockerfile + docker-compose + CI/CD + pre-commit

- **Docker — Best practices for writing Dockerfiles** — multi-stage, layer ordering, .dockerignore. <https://docs.docker.com/develop/develop-images/instructions/>
- **Docker Compose specification** — la spec oficial v2 de compose (ya no es "docker-compose v1" Python). <https://compose-spec.io/>
- **GitHub Actions — Workflow syntax** — toda la sintaxis de `.github/workflows/*.yml`. <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>
- **GitHub Actions — Using a matrix for jobs** — cómo correr Chrome y Firefox en paralelo (lo que pide Hit #7). <https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs>
- **gitleaks** — bloquea commits con secrets. <https://github.com/gitleaks/gitleaks>
- **gitleaks-action** — el wrapper para usarlo en GH Actions. <https://github.com/gitleaks/gitleaks-action>
- **pre-commit framework** — la referencia para el `.pre-commit-config.yaml`. <https://pre-commit.com/>
- **Sigstore / cosign** — firma criptográfica de imágenes Docker, **estándar 2026** para supply chain security (SLSA Level 3). Lo que viene después de gitleaks. <https://docs.sigstore.dev/>

### Hit #7 — Kubernetes Job + CronJob + ConfigMap + PVC

- **Kubernetes — Jobs** — toda la spec de `batch/v1.Job` con backoffLimit, activeDeadlineSeconds, ttlSecondsAfterFinished. <https://kubernetes.io/docs/concepts/workloads/controllers/job/>
- **Kubernetes — CronJob** — schedule syntax + `concurrencyPolicy` + `successfulJobsHistoryLimit`. <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
- **Kubernetes — ConfigMaps** — incluye la sección sobre `immutable: true` (recomendada para producción). <https://kubernetes.io/docs/concepts/configuration/configmap/>
- **Kubernetes — Persistent Volumes** — el modelo PV/PVC + storage classes (`local-path` que viene en k3s). <https://kubernetes.io/docs/concepts/storage/persistent-volumes/>
- **Kubernetes Patterns — Cap. 7: Batch Job + Cap. 8: Periodic Job** (Ibryam & Huß, O'Reilly 2023) — los patterns canónicos para lo que estamos haciendo en este hit. Ver capítulo en el [libro](https://www.oreilly.com/library/view/kubernetes-patterns-2nd/9781098131678/).

### Hit #8 — Paginación + estadísticas + PostgreSQL

- **PostgreSQL Documentation** — manual oficial. La sección [Concurrency Control](https://www.postgresql.org/docs/current/mvcc.html) es relevante para entender por qué inserts concurrentes desde múltiples corridas del CronJob no se pisan. <https://www.postgresql.org/docs/>
- **PostgreSQL en Kubernetes — operadores oficiales:**
  - **CloudNativePG** (recomendado en 2026) — operador de PostgreSQL nativo Kubernetes, mantenido por EDB. <https://cloudnative-pg.io/>
  - **Zalando Postgres Operator** — alternativa madura usada en producción por Zalando. <https://github.com/zalando/postgres-operator>
  - Para el TP les alcanza con un `StatefulSet` simple + `PVC` + `Secret` — los operadores son la forma "production-grade" para que conozcan que existen.
- **Schema migrations:**
  - **Alembic** (Python / SQLAlchemy) — <https://alembic.sqlalchemy.org/>
  - **Flyway** (Java/multi-stack) — <https://documentation.red-gate.com/fd/>
  - **Liquibase** — <https://docs.liquibase.com/>
  - **Refactoring Databases — Ambler & Sadalage** (Addison-Wesley 2006) — el libro fundacional sobre por qué las migrations versionadas son no-negociables en producción. Sigue vigente. <https://databaserefactoring.com/>
- **Estadística básica (mediana, desvío estándar):**
  - **Python `statistics` stdlib** — `statistics.median`, `statistics.stdev`. Sin numpy alcanza para Hit #8. <https://docs.python.org/3/library/statistics.html>
  - **Equivalentes**: [`Math.std` lodash](https://lodash.com/docs#mean) o [`d3.deviation`](https://d3js.org/d3-array/summarize) en Node · [`DescriptiveStatistics`](https://commons.apache.org/proper/commons-math/userguide/stat.html) de Apache Commons Math en Java.

### ADRs

- **Architecture Decision Records — Michael Nygard's collection** — colección canónica con 30+ templates y 100+ ejemplos reales de empresas. <https://github.com/joelparkerhenderson/architecture-decision-record>
- **"Documenting Architecture Decisions"** — Nygard, 2011 — el post fundacional. <https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions>

### Dataset / sitio del TP

- **MercadoLibre Argentina** — <https://www.mercadolibre.com.ar>
