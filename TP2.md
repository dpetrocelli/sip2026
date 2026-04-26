# Trabajo Práctico Nº 1 — Parte 2

## Robustez, Tests, Docker, Kubernetes y CI/CD sobre el scraper de MercadoLibre

**Fecha de Entrega: 02/05/2026**

**Pre-requisitos:**
- Haber entregado la **Parte 1** (Hits #1–#3). Esta segunda parte continúa el mismo proyecto y arranca con el Hit #4 (extracción estructurada a JSON), que es la base sobre la que se construye el resto.
- Haber completado la guía del **TP 0 — Prerrequisitos (k3s)** antes de empezar el Hit #8. Sin un cluster k3s/k3d funcional no podés cumplir esa parte.

> 📚 **Implementación de referencia disponible.** La cátedra publicó una implementación completa que cubre los 8 hits + ADRs + pre-commit + CI + manifests k8s en <https://github.com/dpetrocelli/sip2026/tree/main/reference>. Sirve como vara de corrección y como ejemplo de buenas prácticas (no la copien tal cual — adaptenla a su stack y decisiones).

---

## Requisitos, consideraciones y formato de entrega

Aplican los mismos requisitos generales de la Parte 1, **más** los siguientes:

- **Pipeline de CI/CD obligatorio** (GitHub Actions). Debe correr el scraper en headless contra Chrome y Firefox y publicar los artefactos generados (JSON + screenshots).
- **Dockerfile obligatorio**. La solución debe poder ejecutarse íntegramente desde un contenedor sin necesidad de instalar drivers ni navegadores en la máquina host.
- **Tests automatizados obligatorios** (`pytest` / `JUnit` / `Jest`) corriendo en CI sobre matriz de browsers, con **cobertura ≥ 70 %** medida por la herramienta estándar del lenguaje (`coverage.py`, `jest --coverage`, `jacoco`). El pipeline debe **fallar** si la cobertura cae debajo del umbral.
- **Pre-commit hooks obligatorios** (`pre-commit` framework o equivalente nativo del lenguaje). Como mínimo: `gitleaks` para detectar secrets, y el linter del lenguaje (`ruff` para Python, `eslint` para Node, `checkstyle`/`spotless` para Java). Esto fuerza que los problemas se detecten **antes** de pushear, no recién en CI.
- **Mínimo 3 ADRs** (Architecture Decision Records) en `docs/adr/`, formato Markdown corto (1 página máx cada uno). Como mínimo:
  - `0001-selenium-vs-playwright.md` — por qué eligieron Selenium (y no Playwright/Puppeteer/Cypress).
  - `0002-multi-browser.md` — por qué se exige soporte de Chrome **y** Firefox simultáneo.
  - `0003-k8s-job-vs-docker-compose.md` — por qué Kubernetes Job y no `docker-compose` para el scraping programado.
  - Plantilla recomendada: <https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md>
- Mantener las **buenas prácticas** ya exigidas en Parte 1: explicit waits, selectores en módulo aparte, logs estructurados, no commitear secrets, gitleaks en CI.

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

### Hit #7

Construya un **Dockerfile** que empaquete el scraper junto con Chrome, Firefox y los drivers, de modo que se pueda ejecutar con un único comando:

```bash
docker run --rm -v $(pwd)/output:/app/output ml-scraper:latest --browser firefox
```

Configure un **GitHub Actions workflow** (`.github/workflows/scrape.yml`) que:

1. Construya la imagen Docker.
2. Corra el scraper en headless contra Chrome y Firefox (jobs en paralelo, matriz).
3. Ejecute los tests del Hit #6 y verifique cobertura ≥ 70 %.
4. Publique los JSON, screenshots y reporte de cobertura como **artifacts** del workflow.
5. Falle si gitleaks detecta secrets hardcodeados.

**Pre-commit hooks locales obligatorios.** Agregue un archivo `.pre-commit-config.yaml` (o equivalente) con, como mínimo:

- `gitleaks` — bloquea commits con secrets.
- Linter del lenguaje (`ruff` / `eslint` / `checkstyle`).
- Formatter (`black` / `prettier` / `spotless`).

Documente en el README cómo activarlos: `pre-commit install` (Python/Node) o el equivalente del stack.

---

### Hit #8 — Despliegue en Kubernetes (k3s)

**Pre-requisito:** haber completado el [TP 0](practica-0.html) y tener un cluster k3s o k3d funcional.

Empaquete el scraper construido en el Hit #7 como una carga de trabajo de Kubernetes. El objetivo es ir más allá de "corre en mi máquina con Docker" y demostrar que la solución se puede desplegar en un orquestador.

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
# 1. Construir la imagen Docker (igual que en Hit #7)
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

#### Entregables del Hit #8

- Carpeta `k8s/` con los 4 YAMLs.
- Sección en el README explicando: cómo levantar el cluster (referenciando TP 0), cómo cargar la imagen, cómo aplicar los manifiestos, cómo verificar.
- Captura de pantalla (o asciinema) de `kubectl get jobs` mostrando un Job completado y `kubectl get cronjobs` mostrando el cron activo.
- Bonus: agregar al pipeline de CI una etapa que valide la sintaxis de los YAMLs con `kubectl apply --dry-run=client -f k8s/`.

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

Formato Michael Nygard, 1 página. Copien esto a `docs/adr/0000-template.md` y úsenlo como base para los 3 ADRs obligatorios.

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

**Ejemplo concreto** del primer ADR (`0001-selenium-vs-playwright.md`):

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

### Esqueleto del Dockerfile multi-stage (Hit #7)

Esto es un punto de partida. Adapten al lenguaje. La idea es **multi-stage** para que la imagen final sea lo más chica posible (no necesitan compiladores ni headers en runtime).

```dockerfile
# ============ Stage 1: builder (deps + compile) ============
FROM python:3.13-slim AS builder
WORKDIR /app

# System deps para compilar wheels si hace falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============ Stage 2: runtime (browsers + app) ============
FROM python:3.13-slim AS runtime
WORKDIR /app

# Instalar Chrome, Firefox y deps mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    firefox-esr \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copiar deps de Python desde el builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Usuario no-root (mejor práctica)
RUN useradd -m -u 1000 scraper
USER scraper

COPY --chown=scraper:scraper . .

# Healthcheck — opcional pero recomendado
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import selenium; print('ok')" || exit 1

ENTRYPOINT ["python", "scraper.py"]
CMD ["--browser", "chrome"]
```

**Equivalentes para otros stacks:**
- **Node**: `FROM node:20-slim AS builder` → `npm ci --only=production` → stage runtime con `node:20-slim` + browsers, `USER node`
- **Java**: `FROM maven:3.9-eclipse-temurin-17 AS builder` → `mvn -B package -DskipTests` → stage runtime con `eclipse-temurin:17-jre` + browsers, copiar `.jar`

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

### Esqueleto del workflow de CI (`.github/workflows/scrape.yml`, Hit #7)

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
   - Comandos exactos para reproducir el demo del Hit #8.
3. **Carpeta `docs/adr/`** con como mínimo 3 ADRs.
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

### Hit #9 (Bonus)

Extienda el scraper con cualquiera (o varias) de las siguientes capacidades:

1. **Paginación**: traer los primeros 30 resultados en lugar de 10, navegando hasta 3 páginas.
2. **Comparación de precios**: para cada producto, calcular precio mínimo, máximo, mediana y desvío estándar entre los resultados extraídos. Imprimir tabla resumen.
3. **Histórico con SQLite**: guardar los resultados en una base liviana con timestamp, para detectar cambios de precio entre corridas del CronJob (Hit #8).
4. **Reporte HTML**: generar una página estática (con GitHub Pages publicada por el pipeline) que muestre los resultados de la última corrida en una tabla navegable.
5. **Page Object Model**: refactorizar el scraper para separar el código de navegación (`SearchPage`, `ResultsPage`) del código de extracción y de los tests.
6. **Helm Chart**: empaquetar los manifiestos del Hit #8 como un chart con `values.yaml` parametrizable.

---

## Criterios de evaluación — Parte 2

Total: 100 puntos (Hits #4–#8 + extras obligatorios). El Hit #9 es **bonus** y suma hasta 10 puntos extra sobre el total.

| Criterio | Peso |
|----------|------|
| Hit #4 — extracción estructurada a JSON de los 3 productos con todos los campos | 20 % |
| Hit #5 — manejo robusto de errores (selectores faltantes, timeouts, retries con backoff) | 10 % |
| Hit #6 — tests automatizados + cobertura ≥ 70 % validada en CI | 13 % |
| Hit #7 — Dockerfile funcional con Chrome + Firefox + drivers | 10 % |
| Hit #7 — pipeline CI/CD con matriz de browsers, artifacts y gate de cobertura | 12 % |
| Hit #7 — pre-commit hooks (gitleaks + linter + formatter) configurados y documentados | 5 % |
| Hit #8 — `Job` + `CronJob` + `ConfigMap` + `PVC` corriendo en k3s/k3d | 15 % |
| ADRs (mínimo 3, en `docs/adr/`) | 5 % |
| Modo headless configurable y operativo + checklist de auto-verificación cumplido | 10 % |
| **Hit #9 (bonus, opcional)** — al menos uno de los 6 ítems del Hit #9 | **+10 %** |

---

## Referencias y Bibliografía

- **[SEL]** Selenium Documentation. <https://www.selenium.dev/documentation/>
- **[POM]** Page Object Model — Selenium Wiki. <https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/>
- **[GH-ACTIONS]** GitHub Actions Documentation. <https://docs.github.com/en/actions>
- **[DOCKER]** Docker — Best practices for writing Dockerfiles. <https://docs.docker.com/develop/develop-images/dockerfile_best-practices/>
- **[GITLEAKS]** gitleaks. <https://github.com/gitleaks/gitleaks>
- **[PRECOMMIT]** pre-commit framework. <https://pre-commit.com/>
- **[K3S]** k3s — Lightweight Kubernetes. <https://docs.k3s.io/>
- **[K3D]** k3d — k3s in Docker. <https://k3d.io/>
- **[K8S-JOB]** Kubernetes Jobs. <https://kubernetes.io/docs/concepts/workloads/controllers/job/>
- **[K8S-CRON]** Kubernetes CronJob. <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
- **[ADR]** Architecture Decision Records — Michael Nygard. <https://github.com/joelparkerhenderson/architecture-decision-record>
- **[ML]** MercadoLibre Argentina. <https://www.mercadolibre.com.ar>
