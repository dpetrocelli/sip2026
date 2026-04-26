# Trabajo Práctico Nº 1 — Parte 2

## Robustez, Tests, Docker, Kubernetes y CI/CD sobre el scraper de MercadoLibre

**Fecha de Entrega: 02/05/2026**

**Pre-requisitos:**
- Haber entregado la **Parte 1** (Hits #1–#3). Esta segunda parte continúa el mismo proyecto y arranca con el Hit #4 (extracción estructurada a JSON), que es la base sobre la que se construye el resto.
- Haber completado la guía del **TP 0 — Prerrequisitos (k3s)** antes de empezar el Hit #8. Sin un cluster k3s/k3d funcional no podés cumplir esa parte.

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

| Criterio | Peso |
|----------|------|
| Hit #4 — extracción estructurada a JSON de los 3 productos con todos los campos | 18 % |
| Hit #5 — manejo robusto de errores (selectores faltantes, timeouts, retries con backoff) | 10 % |
| Hit #6 — tests automatizados + cobertura ≥ 70 % validada en CI | 12 % |
| Hit #7 — Dockerfile funcional con Chrome + Firefox + drivers | 10 % |
| Hit #7 — pipeline CI/CD con matriz de browsers, artifacts y gate de cobertura | 10 % |
| Hit #7 — pre-commit hooks (gitleaks + linter + formatter) configurados y documentados | 5 % |
| Hit #8 — `Job` + `CronJob` + `ConfigMap` + `PVC` corriendo en k3s/k3d | 15 % |
| ADRs (mínimo 3, en `docs/adr/`) | 5 % |
| Modo headless configurable y operativo | 5 % |
| Hit #9 (al menos uno de los bonus) | 10 % |

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
