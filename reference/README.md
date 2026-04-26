# TP Selenium MercadoLibre — Implementación de Referencia (Cátedra)

> **Disclaimer importante.** Esta es la **implementación de referencia construida por la cátedra** como vara de corrección del TP de SIP 2026. Su único propósito es servir como criterio interno de evaluación y como recurso para discutir soluciones después de la entrega. **Los alumnos NO deben copiar de acá.** Pueden compararla contra su propia entrega **una vez corregida** para entender qué decisiones tomaríamos nosotros, pero entregar este código (o variaciones cosméticas) cuenta como copia y se sanciona según el régimen académico vigente.

---

## Stack

| Componente | Versión | Notas |
|---|---|---|
| Python | 3.13 | Definido en `pyproject.toml` |
| Selenium | 4.x | Bindings oficiales, Selenium Manager para drivers |
| Browsers | Chrome (Chromium) + Firefox (Gecko) | Multi-browser obligatorio (ver ADR 0002) |
| Test runner | `pytest` + `pytest-cov` | Cobertura mínima 70 % validada en CI |
| Linter / Formatter | `ruff` | Configurado en `pyproject.toml` |
| Container runtime | Docker | Multi-stage build, usuario no-root |
| Orquestador | k3s / k3d | Kubernetes liviano (ver ADR 0003) |
| CI/CD | GitHub Actions | Matriz Chrome/Firefox + coverage gate |
| Pre-commit | `pre-commit` framework | gitleaks + ruff + check-yaml |

---

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `src/` | Código fuente del scraper (browser factory, selectores, extractores, runner principal) |
| `tests/` | Tests automatizados (unitarios + integración) corridos en CI bajo matriz de browsers |
| `hit1/` | Setup inicial: instalación de Selenium + smoke test multi-browser |
| `hit2/` | Multi-browser Browser Factory (`BROWSER=chrome\|firefox`) |
| `hit3/` | Búsqueda + filtros vía DOM en MercadoLibre |
| `hit4/` | Extracción estructurada a JSON (los 6 campos por resultado, 10 resultados por producto) |
| `hit5/` | Robustez: selectores en módulo aparte, manejo de fallos parciales, retries con backoff |
| `hit6/` | Modo headless + tests automatizados + coverage ≥ 70 % |
| `hit7/` | Dockerfile multi-stage + workflow de CI con matriz de browsers + pre-commit |
| `hit8/` | Manifests de Kubernetes: `Job`, `CronJob`, `ConfigMap`, `PVC` |
| `docs/adr/` | Architecture Decision Records (3 oficiales + plantilla) |
| `output/` | Salida de cada corrida: `bicicleta_rodado_29.json`, `iphone_16_pro_max.json`, `geforce_5090.json` |
| `screenshots/` | Capturas generadas por el scraper (evidencia + debugging) |
| `logs/` | Logs estructurados de corridas |
| `.github/workflows/` | Pipeline de CI/CD (`scrape.yml`) |

---

## Cómo correr cada hit

> Cada subcarpeta `hitN/` tiene su propio `README.md` con el detalle. Lo que sigue es solo el índice.

| Hit | Comando rápido | Ver detalle |
|---|---|---|
| #1 | `python -m src.smoke --browser chrome` | `hit1/README.md` |
| #2 | `BROWSER=firefox python -m src.runner` | `hit2/README.md` |
| #3 | `python -m src.runner --product "iPhone 16 Pro Max"` | `hit3/README.md` |
| #4 | `python -m src.runner --all-products --output-dir output/` | `hit4/README.md` |
| #5 | `python -m src.runner --all-products --retries 3` | `hit5/README.md` |
| #6 | `HEADLESS=true python -m src.runner --all-products` | `hit6/README.md` |
| #7 | `docker run --rm -v $(pwd)/output:/app/output ml-scraper:latest --browser firefox` | `hit7/README.md` |
| #8 | `kubectl apply -f hit8/k8s/` | `hit8/README.md` |

> *Placeholder.* Los comandos exactos, variables de entorno y outputs esperados están documentados en cada `hitN/README.md` por los implementadores de cada hit.

---

## Cómo correr los tests

```bash
# Local, browser único
pytest --cov=src --cov-report=html --cov-fail-under=70

# Local, matriz de browsers (igual que CI)
BROWSER=chrome  pytest --cov=src --cov-fail-under=70
BROWSER=firefox pytest --cov=src --cov-fail-under=70

# Dentro del contenedor Docker
docker run --rm ml-scraper:latest pytest --cov=src --cov-fail-under=70
```

> *Placeholder.* La estructura exacta de fixtures, marcadores de pytest y mocks está documentada en `tests/README.md`.

---

## Cómo deployar el Hit #8 en k3d

```bash
# 1. Construir la imagen
docker build -t ml-scraper:latest .

# 2. Importar al cluster k3d (asume cluster llamado 'scraper')
k3d image import ml-scraper:latest -c scraper

# 3. Aplicar todos los manifiestos
kubectl apply -f hit8/k8s/

# 4. Disparar el Job one-off y seguir los logs
kubectl logs -l job-name=scraper-once -f

# 5. Verificar que el CronJob quedó programado
kubectl get cronjobs
```

> *Placeholder.* El recetario completo (incluyendo path para k3s nativo, troubleshooting, verificación del PVC y limpieza) está en `hit8/README.md`.

---

## Architecture Decision Records

Los 3 ADRs oficiales que documentan las decisiones técnicas centrales del proyecto:

- [`docs/adr/0000-template.md`](docs/adr/0000-template.md) — Plantilla en blanco (formato Michael Nygard)
- [`docs/adr/0001-selenium-vs-playwright.md`](docs/adr/0001-selenium-vs-playwright.md) — Por qué Selenium y no Playwright/Puppeteer/Cypress
- [`docs/adr/0002-multi-browser-chrome-firefox.md`](docs/adr/0002-multi-browser-chrome-firefox.md) — Por qué soportar Chrome y Firefox simultáneamente
- [`docs/adr/0003-k8s-job-vs-docker-compose.md`](docs/adr/0003-k8s-job-vs-docker-compose.md) — Por qué Kubernetes Job/CronJob en lugar de docker-compose + cron del host

---

## Productos objetivo

El scraper procesa los **3 productos definidos en la consigna del TP**, idénticos en Parte 1 y Parte 2:

1. **Bicicleta rodado 29** → `output/bicicleta_rodado_29.json`
2. **iPhone 16 Pro Max** → `output/iphone_16_pro_max.json`
3. **GeForce RTX 5090** → `output/geforce_5090.json`

Cada archivo es un array JSON con los **primeros 10 resultados** filtrados, donde cada elemento tiene los 6 campos definidos en el Hit #4: `titulo`, `precio`, `link`, `tienda_oficial`, `envio_gratis`, `cuotas_sin_interes`.

---

## Licencia

**MIT License.** Es la elección estándar para material de cátedra: permisiva, compatible con la mayoría de proyectos en los que los alumnos podrían querer reusar fragmentos en el futuro, sin reciprocidad obligatoria (a diferencia de GPL) y sin cláusulas de atribución pesadas (a diferencia de Apache 2.0). Para un repo educativo es la combinación correcta de "tomalo y aprendé" con "atribuí cuando uses partes sustanciales".

Ver archivo `LICENSE` en la raíz del repo (a agregar por la cátedra).

---

## Para los alumnos

### Qué se espera de tu entrega

Tu repo (no este) tiene que cumplir todo lo listado en la consigna oficial: los 8 hits + bonus opcional, README raíz documentando cómo reproducir cada parte, carpeta `docs/adr/` con **mínimo 3 ADRs propios** (no copiados de acá), pipeline de CI verde con coverage ≥ 70 %, Dockerfile funcional, manifests de Kubernetes corriendo en k3s/k3d, y video de demo.

**Lo que no se acepta:**
- Coverage por debajo del 70 %.
- Pipeline de CI roto en `main`.
- Secrets hardcodeados (gitleaks los detecta y la entrega se rechaza directo).
- ADRs genéricos copiados de internet sin contexto del proyecto propio.
- "Funciona solo en Chrome" — la matriz exige Firefox también.

### Links oficiales

- Consigna del TP — Parte 1 (Hits #1–#3): <https://dpetrocelli.github.io/sip2026/practica-1.html>
- Consigna del TP — Parte 2 (Hits #4–#9): <https://dpetrocelli.github.io/sip2026/practica-2.html>
- TP 0 — Prerrequisitos de Kubernetes (k3s): <https://dpetrocelli.github.io/sip2026/practica-0.html>
- Sitio principal de la materia: <https://dpetrocelli.github.io/sip2026/>

### Recordatorio de la rúbrica (Parte 2)

| Criterio | Peso |
|---|---|
| Hit #4 — extracción JSON con todos los campos | 18 % |
| Hit #5 — manejo robusto de errores + retries con backoff | 10 % |
| Hit #6 — tests + coverage ≥ 70 % validada en CI | 12 % |
| Hit #7 — Dockerfile con Chrome + Firefox + drivers | 10 % |
| Hit #7 — pipeline CI/CD con matriz + artifacts + coverage gate | 10 % |
| Hit #7 — pre-commit hooks configurados y documentados | 5 % |
| Hit #8 — Job + CronJob + ConfigMap + PVC en k3s/k3d | 15 % |
| ADRs (mínimo 3) | 5 % |
| Modo headless configurable | 5 % |
| Hit #9 (al menos un bonus) | 10 % |

Antes de pedir ayuda en Discord: leé el [TP 0](https://dpetrocelli.github.io/sip2026/practica-0.html) y la sección de troubleshooting que ya tiene los 4 errores típicos resueltos.
