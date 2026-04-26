# TP 1 · Parte 1 — Lecciones del curso

Tras corregir las 4 entregas de la Parte 1 (TP1 · Hits #1–#3, fecha 25/04/2026), aparecieron varios patrones repetidos que vale la pena explicitar para que no se repitan en la **Parte 2**. Este documento es **anónimo** — no nombra equipos, solo describe el bug, por qué duele, y cómo prevenirlo.

> Si te ves reflejado en alguno de estos puntos: no es un reproche, es la oportunidad de cerrarlo antes del 02/05.

---

## 1. `time.sleep(N)` disfrazado

**Patrón que vimos:**

```python
# o en JS: setTimeout(() => {}, 600)
time.sleep(0.6)  # "para que el dropdown termine de abrirse"
```

**Por qué duele:**
- La consigna prohíbe sleep como mecanismo de sincronización principal — y este lo es.
- En CI con red lenta, 0.6s no alcanza → test falla intermitentemente.
- En máquina rápida, 0.6s es desperdicio puro → corridas más lentas.

**Cómo se hace bien:**

```python
WebDriverWait(driver, 5).until(
    EC.attribute_to_be((By.ID, "andes-dropdown"), "data-state", "open")
)
# o EC.element_to_be_clickable, presence_of_element_located, text_to_be_present_in_element
```

La pregunta clave que reemplaza al `sleep`: **"¿qué cosa específica estoy esperando?"**. Esa cosa es la condición que va dentro del `until`.

---

## 2. Selectores hardcodeados inline en cada función

**Patrón:**

```python
def aplicar_filtro_nuevo(driver):
    el = driver.find_element(By.XPATH, "//span[contains(text(), 'Nuevo')]/..")
    el.click()

def aplicar_filtro_tienda(driver):
    el = driver.find_element(By.XPATH, "//span[contains(text(), 'Tienda Oficial')]/..")
    el.click()
```

Mismo XPath repetido en 6 lugares. ML cambia el DOM → 6 lugares para arreglar.

**Cómo se hace bien:** un módulo `selectors.py` (o `Locators.java`, `selectors.ts`) con constantes:

```python
# selectors.py
FILTRO_NUEVO_LINK = "//div[@aria-label='Filtros']//a[contains(., 'Nuevo')]"
FILTRO_TIENDA_OFICIAL_CHECKBOX = "//div[@aria-label='Filtros']//label[contains(., 'Tienda oficial')]/input"
RESULTADO_CARD = "li.ui-search-layout__item"
RESULTADO_TITULO = ".ui-search-item__title"
```

> **Cuidado con el nombre.** En Python no llames al archivo `selectors.py` si va a ser importable como módulo top-level del proyecto — ese nombre choca con el `selectors` de la stdlib. Usá `ml_selectors.py` o ponelo dentro de un paquete (`scraper/selectors.py`).

---

## 3. Asserts débiles que pasan sin probar nada

**Patrón:**

```python
def test_filtros_aplicados(driver):
    safe_click(driver, "...nuevo...")    # silencia TimeoutException
    safe_click(driver, "...tienda...")
    titulos = driver.find_elements(By.CSS_SELECTOR, ".titulo")
    assert len(titulos) >= 3
```

**Por qué este test no prueba nada:**
1. `safe_click` silencia errores → si el filtro NO se aplica, el test pasa igual.
2. `len >= 3` siempre es True porque ML siempre devuelve >3 resultados, con o sin filtro.

**Resultado:** el test se ejecuta verde 1000 veces y nunca probó que los filtros funcionen.

**Cómo se hace bien:** el assert tiene que validar la **propiedad que el filtro garantiza**, no la cantidad de resultados.

```python
# Después de aplicar "Tienda oficial":
cards = driver.find_elements(By.CSS_SELECTOR, "li.ui-search-layout__item")
badges = [c.find_elements(By.CSS_SELECTOR, ".ui-search-item__official-store-label") for c in cards]
assert all(len(b) >= 1 for b in badges), "Filtro 'Tienda oficial' no se aplicó"

# o validar que la URL cambió:
assert "official_store=all" in driver.current_url
```

---

## 4. `print()` en lugar de `logging`

**Patrón:**

```python
print(f"Buscando {producto}")
print(f"Resultados: {len(resultados)}")
print(f"ERROR: timeout")
```

**Por qué duele:**
- La consigna pide "registros estructurados con niveles INFO/WARN/ERROR".
- `print` no tiene niveles → no podés filtrar el log para ver solo ERRORs.
- `print` no se rota → si el scraper corre como CronJob (Hit #8), el archivo crece infinito.
- En CI, los `print` se mezclan con stdout de pytest y se vuelven ilegibles.

**Cómo se hace bien:**

```python
# Setup en main.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler("logs/scraper.log", maxBytes=2_000_000, backupCount=3),
        logging.StreamHandler(),
    ],
)

# En cualquier módulo
logger = logging.getLogger(__name__)
logger.info("Buscando %s", producto)          # INFO
logger.warning("Timeout en %s, reintentando", selector)  # WARN
logger.error("Falló todo: %s", exc, exc_info=True)        # ERROR + stacktrace
```

Equivalentes: SLF4J + Logback en Java, `pino` o `winston` en Node.

---

## 5. `.gitignore` ausente o incompleto

**Patrones que vimos:**

| Lo que se commiteó por error | Cómo prevenirlo |
|---|---|
| `__pycache__/`, `*.pyc` | Línea `__pycache__/` en `.gitignore` |
| `target/` (Maven, ~MB de `.class` files) | Línea `target/` en `.gitignore` |
| `.venv/`, `venv/`, `node_modules/` | Líneas estándar |
| `output/`, `screenshots/`, `logs/` | Líneas según paths del proyecto |
| `requeriments.txt` (typo) | Renombrar a `requirements.txt` y verificar que pip lo encuentre |

**Plantilla mínima por stack:**

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
htmlcov/
.coverage
.pytest_cache/

# Node
node_modules/
dist/
.npm/

# Java/Maven
target/
*.class
.idea/

# IDE
.vscode/
*.swp

# Output del scraper
output/
screenshots/
logs/

# Secretos
.env
*.pem
```

Quien empezó con `.gitignore` desde el commit 0 evitó este 100%.

---

## 6. README raíz vacío o ausente

**Patrón típico:**

```markdown
# TP1-Selenium
TP1 Selenium
```

Eso es todo el README raíz. La consigna pide explícitamente:

- **Tabla de integrantes con legajo.**
- Stack utilizado.
- Cómo correr el proyecto (3 hits, requisitos previos, comandos).
- Decisiones de diseño tomadas y por qué.
- Comparativa Chrome vs Firefox.
- Herramientas de IA usadas y para qué.
- Link al video.

Está todo en el [esqueleto del README en la consigna de Parte 1](https://dpetrocelli.github.io/sip2026/practica-1-parte-1.html#estructura-del-repositorio-template-obligatorio). Coypy-paste y completar.

---

## 7. Validar contra **un solo browser** cuando el Hit #2 pide ambos

**Patrón:**
- Screenshot solo de Chrome.
- Tests solo en Chrome.
- README dice "se probó en Chrome y Firefox" pero no hay evidencia.

**Por qué duele:** todo el sentido del Hit #2 es la **portabilidad** del Browser Factory. Si solo probás Chrome, no validaste nada.

**Cómo se hace bien:** correr la suite contra los dos browsers y commitear ambos screenshots y outputs:

```bash
BROWSER=chrome python -m pytest && cp output/* output/chrome-run/
BROWSER=firefox python -m pytest && cp output/* output/firefox-run/
```

En CI esto se hace con una matriz (Hit #7):

```yaml
strategy:
  matrix:
    browser: [chrome, firefox]
```

---

## 8. Ningún equipo entregó Dockerfile en Parte 1

El Dockerfile en Parte 1 era **deseable, no obligatorio** — pero los 5 % de bonus quedaron arriba de la mesa para los 4 equipos. **En Parte 2 es obligatorio**, así que conviene empezar a armarlo desde ya.

**Mínimo viable:**

```dockerfile
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable firefox-esr ca-certificates fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 scraper
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
USER scraper
COPY . .
ENTRYPOINT ["python", "main.py"]
```

**Trampa que nos comimos en la implementación de referencia:** **NO uses `chromium` de Debian trixie** — tiene un bug de crashpad que hace que `google-chrome --headless` muera con `--database is required`. **Usá Google Chrome stable** desde el repo oficial:

```dockerfile
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y google-chrome-stable
```

Y **el usuario non-root necesita `--create-home`** — sin home dir, Chrome explota con `cannot touch '/home/user/.local/...'`.

---

## 9. Ningún equipo (excepto uno) tenía CI workflow

Sin CI:
- No sabés si tu código compila / corre / pasa tests en ambiente limpio.
- El profe corrige a mano lo que un workflow de 30 líneas puede automatizar.

**Mínimo CI para Parte 2** (que se pide explícito):

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-24.04
    strategy: { matrix: { browser: [chrome, firefox] } }
    steps:
      - uses: actions/checkout@v4
      - uses: gitleaks/gitleaks-action@v2
      - run: docker build -t scraper:ci .
      - run: docker run --rm -e BROWSER=${{ matrix.browser }} -e HEADLESS=true scraper:ci pytest --cov-fail-under=70
```

---

## 10. Nadie incluyó ADRs

Los ADRs (Architecture Decision Records) van a ser **5 % de Parte 2**. Hay [plantilla en la consigna](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html#material-de-apoyo) y [ejemplos completos en el repo de referencia](https://github.com/dpetrocelli/sip2026/tree/main/reference/docs/adr).

**Truco:** documenten decisiones que ya tomaron en Parte 1, no inventen nuevas. Por ejemplo:
- *"¿Por qué cerramos el banner de cookies con click vs con `execute_script`?"* → ADR-1.
- *"¿Por qué `WebDriverWait(driver, 15)` y no 10?"* → ADR-2.
- *"¿Por qué Job y no Deployment?"* → ADR-3 (Hit #8).

5 minutos por ADR, escribiendo lo que ya hicieron.

---

## TL;DR — checklist rápida pre-entrega Parte 2

Antes del push final del 02/05, asegurate de tener:

- [ ] Cero `time.sleep` (o `setTimeout`/`Thread.sleep`) en código no-test
- [ ] Selectores en un único módulo (`ml_selectors.py` / `Locators.java` / `selectors.ts`)
- [ ] Tests con asserts que prueben **propiedades**, no cantidades
- [ ] `logging` con niveles INFO/WARN/ERROR + rotación a archivo
- [ ] `.gitignore` completo (sin `__pycache__/`, `target/`, `node_modules/`, `.venv/`, `output/`, `logs/`)
- [ ] README raíz con integrantes, stack, cómo correr, decisiones, Chrome vs Firefox, IA usada, link al video
- [ ] Screenshots de **ambos** browsers
- [ ] Dockerfile multi-stage funcional con Chrome + Firefox + drivers + usuario non-root con home dir
- [ ] CI workflow con matriz Chrome+Firefox + gitleaks + tests con coverage ≥ 70 %
- [ ] 3 ADRs en `docs/adr/`
- [ ] Manifests `k8s/` + evidencia del Job corriendo en cluster local (kubectl get jobs + logs)
- [ ] Pre-commit con gitleaks + linter + formatter
- [ ] Comparado contra el comparador de la cátedra (`python /tmp/sip-ref/reference/tooling/compare.py --student .`)
