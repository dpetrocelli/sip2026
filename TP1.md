# Trabajo Práctico Nº 1 — Parte 1

## Automatización Web con Selenium — Pruebas E2E multi-browser sobre MercadoLibre

**Fecha de Entrega: 25/04/2026 (entrega cerrada)**

> ✅ **Entrega cerrada.** Esta consigna queda como referencia. El trabajo continúa en la [Parte 2](practica-1-parte-2.html) (Hits #4–#9, entrega 02/05/2026), que **requiere** haber completado el [TP 0 — Prerrequisitos k3s](practica-0.html) antes del Hit #8.
>
> 📚 La cátedra publicó la **implementación de referencia** completa de los 8 hits en <https://github.com/dpetrocelli/sip2026/tree/main/reference>, junto con un comparador automático (`tooling/compare.py`) que pueden usar para auto-evaluarse antes de entregar la Parte 2.

---

## Requisitos, consideraciones y formato de entrega

- **Integrar herramientas de IA en su ciclo de vida de desarrollo** (Cursor, ChatGPT/Codex, Claude, GitHub Copilot, etc.). Se espera que las utilicen como asistentes para codificar, depurar y documentar. En el informe, mencionen qué herramientas usaron y cómo les ayudaron.
- **Se puede implementar con cualquier lenguaje que tenga binding oficial de Selenium**: Python, Java o TypeScript/Node.js.
- **Deben incluir una grabación en video** subida al repositorio donde se muestre la ejecución del scraper en ambos navegadores y se expliquen las decisiones de diseño.
- **Pruebas Unitarias y de Integración:** incluir un conjunto mínimo de pruebas automatizadas (`pytest` / `JUnit` / `Jest`) que validen que el flujo extrae al menos N resultados y que los datos cumplen el schema esperado.
- Generar un **informe** que incluya: estrategia de selectores, manejo de timeouts y elementos faltantes, comparación entre Chrome y Firefox, métricas de tiempo de ejecución por browser, y conclusiones.
- Mantener un **repositorio público** en GitHub/GitLab/Bitbucket. Cada Hit debe contar con una carpeta y un README.md explicativo.
  - El README.md debe incluir como mínimo: instrucciones para ejecutar el proyecto, requisitos previos (drivers, versiones), y decisiones de diseño tomadas.
- Compilar la aplicación para ejecución desde la terminal, con recursos preparados para ser desplegados directamente sin necesidad de abrir un IDE.
- **Empaquetar la solución en un Dockerfile** que permita ejecutar el scraper con `docker run` (deseable desde Parte 1, obligatorio en Parte 2). Esto facilita la evaluación uniforme entre proyectos en distintos lenguajes.
- Gestionar y mantener **registros de actividades (logs)** en consola y archivo, con niveles INFO/WARN/ERROR.
- **Seguridad:**
  - No commitear `.env`, credenciales ni secrets al repositorio. Configurar `.gitignore` apropiado desde el inicio.
  - Incluir [gitleaks](https://github.com/gitleaks/gitleaks) en el pipeline de CI — si detecta un secret hardcodeado, el pipeline debe fallar.
  - Respetar el `robots.txt` del sitio y aplicar throttling razonable entre requests.

---

## Contenidos del programa relacionados

- Automatización de navegadores web y testing E2E.
- Protocolo WebDriver (W3C) y arquitectura cliente/servidor de Selenium.
- DOM, selectores CSS y XPath.
- Manejo de asincronía en la web: explicit waits vs implicit waits vs sleeps.
- Patrones de diseño aplicados a testing: Browser Factory.

---

## Práctica

La automatización de navegadores es una técnica fundamental para validar aplicaciones web end-to-end, generar datasets a partir de sitios públicos, y verificar el comportamiento de un mismo sistema sobre distintos motores de renderizado.

**Selenium WebDriver** se ha convertido en el estándar de facto: define un protocolo (W3C WebDriver) que cualquier navegador puede implementar, y expone bindings en múltiples lenguajes para controlar el navegador como si fuera un usuario real.

En esta **Parte 1** vamos a construir, de forma incremental, las bases del scraper multi-browser sobre MercadoLibre Argentina: setup de Selenium, Browser Factory para Chrome y Firefox, y aplicación de filtros vía DOM con captura de screenshots.

El sitio elegido (mercadolibre.com.ar) es público, no requiere autenticación para buscar, y presenta los desafíos clásicos del scraping moderno: contenido renderizado por JavaScript, selectores que cambian, lazy loading, y diferencias sutiles entre navegadores.

**Productos objetivo:**

1. `Bicicleta rodado 29`
2. `iPhone 16 Pro Max`
3. `GeForce RTX 5090`

---

## Conceptos mínimos antes de empezar

Si nunca usaste Selenium, leé estos 4 conceptos. Te van a ahorrar el 80 % de los problemas que vimos en entregas anteriores.

### 1) Qué es WebDriver

**WebDriver** es un protocolo estandarizado por la W3C que permite a un programa controlar un navegador como si fuera un usuario humano: clickear, escribir, navegar, leer el DOM. Selenium es la implementación más popular del cliente, pero también existen Playwright, Puppeteer, Cypress.

Arquitectura: tu código → biblioteca cliente (Selenium) → driver del browser (`chromedriver` / `geckodriver`) → browser. El driver es un proceso aparte que traduce el protocolo HTTP de WebDriver a comandos nativos del browser.

### 2) Explicit waits vs `time.sleep` (esto te bajan la nota si lo mezclás mal)

Una página web moderna **no termina de cargar** en un instante: hay JavaScript ejecutándose, requests AJAX que tardan, elementos que aparecen tarde. Hay 3 estrategias para sincronizar:

| Estrategia | Qué hace | Cuándo usarla |
|------------|----------|---------------|
| `time.sleep(N)` (sleep duro) | Esperás N segundos fijos pase lo que pase | **Casi nunca.** Lento si N es grande, frágil si N es chico. |
| **Explicit wait** (`WebDriverWait` + `expected_conditions`) | Esperás hasta que **una condición específica** se cumpla, con un timeout máximo | **Siempre.** Es el patrón correcto. |
| Implicit wait | Configurás un timeout global para "buscar elementos" | Cómodo pero peligroso — se mezcla raro con explicit waits |

**Regla**: cada vez que estés por escribir `sleep(2)`, preguntate "¿qué cosa estoy esperando?" y reemplazalo por un `WebDriverWait` con `EC.element_to_be_clickable(...)` / `EC.visibility_of_element_located(...)` / `EC.presence_of_element_located(...)`.

### 3) Selectores estables vs frágiles

```html
<!-- Frágil: clase auto-generada que cambia con cada deploy de ML -->
<div class="ui-search-result__1xY7Z">...</div>

<!-- Robusto: estructura semántica + atributos data-* -->
<li class="ui-search-layout__item">
  <h2 class="ui-search-item__title">...</h2>
</li>
```

| Tipo de selector | Robustez | Cuándo |
|------------------|----------|--------|
| `data-testid="..."` | ⭐⭐⭐ Máxima | Si el sitio los expone (ML no) |
| Estructura semántica (`h2.ui-search-item__title`) | ⭐⭐ Media-alta | Patrón principal del TP |
| Clase con sufijo random (`.ui-search-result__1xY`) | ⭐ Baja | **Evitar** |
| XPath posicional (`/div/div[3]/span[2]`) | ⭐ Baja | **Evitar** |

### 4) Headless vs headed

- **Headed** (default): el browser tiene ventana gráfica visible. Útil para desarrollar y debuggear.
- **Headless** (`--headless`): el browser corre sin UI. Imprescindible para CI/CD y servidores. Comportamiento ~99 % igual al headed, **pero**: algunos sitios detectan headless y lo bloquean (ML lo hace si no seteás un User-Agent custom). Lo van a sufrir en Parte 2 cuando integren con CI.

---

### Hit #1

Configure un proyecto en el lenguaje de su elección con Selenium WebDriver y los drivers correspondientes (`chromedriver` y `geckodriver`, o usar `webdriver-manager` / `Selenium Manager`).

Escriba un script que abra **Chrome**, navegue a `https://www.mercadolibre.com.ar`, busque el producto `bicicleta rodado 29`, espere a que cargue la página de resultados, e imprima por consola el título de los primeros 5 productos listados.

Use **explicit waits** (`WebDriverWait` + `expected_conditions`). Está prohibido el uso de `time.sleep()` (o equivalentes) como mecanismo principal de sincronización.

---

### Hit #2

Refactorice el código del Hit #1 para introducir una **Browser Factory**: una función o clase que reciba como parámetro el nombre del navegador (`chrome` o `firefox`) y devuelva una instancia de WebDriver correctamente configurada.

El parámetro debe poder pasarse por línea de comandos o variable de entorno (`BROWSER=firefox python scraper.py`).

Verifique que el script funcione exactamente igual contra **Chrome** y **Firefox**. Documente en el informe cualquier diferencia encontrada (selectores que se rompen, comportamiento distinto de waits, etc.).

---

### Hit #3

Modifique el scraper para aplicar los siguientes **filtros** sobre la página de resultados, después de la búsqueda:

- **Condición**: `Nuevo`
- **Tienda oficial**: `Sí` (solo productos vendidos por tiendas oficiales)
- **Ordenar por**: `Más relevantes`

La interacción con los filtros debe hacerse navegando el DOM (clicks reales sobre los links/checkboxes), **no** modificando la URL a mano. Esto valida que el flujo funciona como lo haría un usuario.

Capture un **screenshot** de la página de resultados ya filtrada y guárdelo como `screenshots/<producto>_<browser>.png`.

---

## Output esperado por hit (autoverificación)

Antes de subir al repo, validá que tu solución cumpla esto. Si algo no aparece, te falta algo.

### Hit #1

Por consola:

```
[INFO] Iniciando scraper en chrome
[INFO] Navegando a https://www.mercadolibre.com.ar
[INFO] Búsqueda: 'bicicleta rodado 29'
1. Bicicleta Mountain Bike Rodado 29 21 Velocidades ...
2. Bicicleta Mtb Rodado 29 Aluminio Shimano 21v ...
3. ...
```

### Hit #2

Mismo output del Hit #1, pero ejecutable contra ambos browsers:

```bash
BROWSER=chrome python scraper.py    # ó npm run scraper -- --browser chrome
BROWSER=firefox python scraper.py
```

Los dos comandos deben **funcionar idéntico** y producir títulos.

### Hit #3

- Console output muestra que los 3 filtros (Nuevo, Tienda oficial, Más relevantes) se aplicaron — debería ser visible en logs o con un dump de la URL final.
- Carpeta `screenshots/` con como mínimo:
  - `screenshots/bicicleta_rodado_29_chrome.png`
  - `screenshots/bicicleta_rodado_29_firefox.png`
- En la imagen tiene que verse el panel lateral de filtros con "Nuevo" y la "Tienda oficial" tildados.

---

## Common pitfalls (cosas con las que se choca todo el mundo)

### MercadoLibre detecta Chrome headless y devuelve empty-state

Si corrés en headless sin User-Agent custom, ML responde con HTML pero **sin resultados de búsqueda**. Workaround:

```python
options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
```

Equivalente en JS y Java. Lo van a necesitar sí o sí en CI (Parte 2).

### Banner de cookies intercepta clicks

ML muestra un banner gigante de "Aceptar cookies" que cubre los filtros. Tres caminos posibles:
1. **Aceptar el banner** con un click sobre el botón (más natural).
2. **Click forzado por JavaScript** (`driver.execute_script("arguments[0].click();", element)`) — bypassa la intercepción pero es un anti-pattern leve.
3. **Esperar que el banner desaparezca solo** después de un click random fuera (frágil).

La opción 1 es la limpia. La 2 es válida si documentan por qué.

### Geographic redirect a otros TLDs

Si tu IP no resuelve a Argentina, ML te redirige a `mercadolibre.com.mx` o `.com.br`. Forzá:

```python
driver.get('https://www.mercadolibre.com.ar/')
# y agregá el header Accept-Language
options.add_argument('--accept-lang=es-AR')
```

### Lazy loading de resultados

Los resultados después del 5to-6to a veces no están en el DOM hasta que scrolleás. Si extraen 10, hagan scroll antes (`driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")`) o esperen a que `len(elementos) >= 10`.

### Selectores que cambian al refresh

Si copiaron una clase como `.ui-search-result__1xY7Z` con sufijo aleatorio, **se va a romper en producción**. Usen estructura semántica (`li.ui-search-layout__item h2`) o atributos estables.

### Timeouts diferentes en Chrome y Firefox

Firefox tarda ~30 % más en cargar la primera página (es así, no es bug suyo). Si pusieron `WebDriverWait(driver, 5)` y funciona en Chrome pero falla en Firefox, suban el timeout a 10-15s.

---

## Estructura del repositorio (template obligatorio)

Esto es lo mínimo que esperamos ver al clonar el repo:

```
.
├── README.md               ← integrantes, cómo correr, decisiones, link al video
├── .gitignore              ← venv/, node_modules/, target/, __pycache__/, .env
├── requirements.txt / package.json / pom.xml
├── hit1/
│   ├── README.md           ← qué hace, cómo correr
│   └── scraper.<py|js|java>
├── hit2/
│   ├── README.md
│   ├── browser_factory.<py|js|java>
│   └── scraper.<py|js|java>
├── hit3/
│   ├── README.md
│   └── scraper.<py|js|java>
└── screenshots/
    ├── bicicleta_rodado_29_chrome.png
    └── bicicleta_rodado_29_firefox.png
```

### README raíz — esqueleto sugerido

````markdown
# TP 1 — Selenium MercadoLibre — <Nombre del equipo>

## Integrantes

| Nombre | Legajo |
|--------|--------|
| ...    | ...    |

## Stack
- Lenguaje: Python 3.13 / Node 20 / Java 17
- Selenium: 4.27
- Tests: pytest / jest / junit (Parte 2)

## Cómo correr

### Requisitos previos
- Chrome y Firefox instalados (o usar el contenedor del Hit #7 — Parte 2)
- Python 3.13 / Node 20 / Java 17

### Ejecución
```bash
# Hit 1
cd hit1 && BROWSER=chrome python scraper.py

# Hit 2
cd hit2 && BROWSER=firefox python scraper.py

# Hit 3
cd hit3 && BROWSER=chrome python scraper.py
```

## Decisiones de diseño
... (qué eligieron y por qué — ej: por qué `WebDriverWait` con timeout 15s, por qué `data-*` no aplicaba)

## Comparativa Chrome vs Firefox
| Aspecto | Chrome | Firefox |
|---------|--------|---------|
| Tiempo del Hit #3 | ... | ... |
| Diferencias en selectores | ... | ... |

## Herramientas de IA usadas
- Cursor / Claude / Copilot — para qué la usamos: ...
- Prompts no triviales documentados en `docs/ai-usage.md`

## Video explicativo
[Link YouTube unlisted]

## Limitaciones conocidas
- ...
````

---

## Cómo entregar

1. **Push final al repo público** (GitHub/GitLab) antes del 25/04/2026 23:59 ART.
2. **README raíz** completo siguiendo el esqueleto de arriba.
3. **Video** subido a YouTube (unlisted) o equivalente, mostrando los 3 hits en ejecución y comentando las decisiones. Link en el README.
4. **Mensaje en el canal Discord de la materia** con el link al repo.

> 📡 **Canal Discord de la materia (consultas + entregas):** <https://discord.com/channels/1482135908508500148/1482135909456679139>
> Antes de preguntar, revisá la sección **Common pitfalls** — el 70 % de las dudas están resueltas ahí.

---

## Criterios de evaluación — Parte 1

| Criterio | Peso |
|----------|------|
| Hit #1 — setup, navegación, búsqueda y lectura de títulos | 15 % |
| Hit #2 — Browser Factory funcionando contra Chrome **y** Firefox sin cambios de código | 25 % |
| Hit #3 — filtros aplicados correctamente vía DOM (nuevo + tienda oficial) y screenshot | 30 % |
| Infra base — calidad de código (waits explícitos, selectores en módulo aparte, sin `time.sleep`) + README/informe/video explicativo + Dockerfile básico (opcional en Parte 1) | 30 % |

---

## Referencias y Bibliografía

- **[SEL]** Selenium Documentation. <https://www.selenium.dev/documentation/>
- **[W3C-WD]** W3C WebDriver Specification. <https://www.w3.org/TR/webdriver2/>
- **[CSS-SEL]** MDN — CSS Selectors. <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors>
- **[XPATH]** MDN — XPath. <https://developer.mozilla.org/en-US/docs/Web/XPath>
- **[GITLEAKS]** gitleaks. <https://github.com/gitleaks/gitleaks>
- **[ROBOTS]** The Robots Exclusion Protocol. <https://www.rfc-editor.org/rfc/rfc9309>
- **[ML]** MercadoLibre Argentina. <https://www.mercadolibre.com.ar>
