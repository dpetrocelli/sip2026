# Trabajo Práctico — Automatización Web con Selenium

## Pruebas E2E multi-browser sobre MercadoLibre

**Fecha de Entrega: a definir**

---

## Requisitos, consideraciones y formato de entrega

- **Integrar herramientas de IA en su ciclo de vida de desarrollo** (Cursor, ChatGPT/Codex, Claude, GitHub Copilot, etc.). Se espera que las utilicen como asistentes para codificar, depurar y documentar. En el informe, mencionen qué herramientas usaron y cómo les ayudaron.
- **Se puede implementar con cualquier lenguaje que tenga binding oficial de Selenium**: Python, Java o TypeScript/Node.js.
- **Deben incluir una grabación en video** que se debe subir al repositorio donde se muestre la ejecución del scraper en ambos navegadores y se expliquen las decisiones de diseño (selectores elegidos, manejo de waits, estrategia de extracción).
- **Pruebas Unitarias y de Integración:** Incluir un conjunto mínimo de pruebas automatizadas (`pytest` / `JUnit` / `Jest`) que validen que el flujo de scraping extrae al menos N resultados y que los datos cumplen el schema esperado.
- Generar un **informe detallado** que incluya: estrategia de selectores, manejo de timeouts y elementos faltantes, comparación entre Chrome y Firefox (diferencias encontradas, si las hubo), métricas de tiempo de ejecución por browser, y conclusiones.
- Mantener un **repositorio público** en un servicio de control de versiones como GitHub, Bitbucket o GitLab. Cada ejercicio (Hit #) debe contar con una carpeta y un README.md explicativo.
  - El README.md de cada Hit debe incluir como mínimo: instrucciones para ejecutar el proyecto, requisitos previos (drivers, versiones), y decisiones de diseño tomadas.
- Compilar la aplicación para ejecución desde la terminal, con recursos preparados para ser desplegados directamente sin necesidad de abrir un IDE.
- Implementar un **pipeline de CI/CD** que automatice la ejecución del scraping con cada nueva versión de código (GitHub Actions). El pipeline debe correr el scraper en modo headless contra ambos browsers y publicar los artefactos generados (JSON/CSV + screenshots).
- Proporcionar un **endpoint público o reporte público** (puede ser una página de GitHub Pages generada por el pipeline) que muestre los últimos resultados extraídos.
- Gestionar y mantener **registros de actividades (logs)** en consola y archivo, con niveles INFO/WARN/ERROR.
- **Seguridad:**
  - No commitear `.env`, credenciales ni secrets al repositorio. Configurar `.gitignore` apropiado desde el inicio.
  - Si el ejercicio requiere autenticación contra MercadoLibre (no es el caso para esta consigna), gestionar credenciales por GitHub Secrets.
  - Incluir [gitleaks](https://github.com/gitleaks/gitleaks) en el pipeline de CI — si detecta un secret hardcodeado, el pipeline debe fallar.
  - Respetar el `robots.txt` del sitio y aplicar throttling razonable entre requests para no generar carga indebida.

---

## Contenidos del programa relacionados

- Automatización de navegadores web y testing E2E.
- Protocolo WebDriver (W3C) y arquitectura cliente/servidor de Selenium.
- DOM, selectores CSS y XPath.
- Manejo de asincronía en la web: explicit waits vs implicit waits vs sleeps.
- Patrones de diseño aplicados a testing: Page Object Model, Browser Factory.
- Headless browsing y ejecución en pipelines CI/CD.

---

## Práctica

La automatización de navegadores es una técnica fundamental para validar aplicaciones web end-to-end, generar datasets a partir de sitios públicos, y verificar el comportamiento de un mismo sistema sobre distintos motores de renderizado.

**Selenium WebDriver** se ha convertido en el estándar de facto: define un protocolo (W3C WebDriver) que cualquier navegador puede implementar, y expone bindings en múltiples lenguajes para controlar el navegador como si fuera un usuario real.

En este TP vamos a construir, de forma incremental, un scraper multi-browser que busque productos en MercadoLibre Argentina, aplique filtros, y extraiga los resultados de forma estructurada.

El sitio elegido (mercadolibre.com.ar) es público, no requiere autenticación para buscar, y presenta los desafíos clásicos del scraping moderno: contenido renderizado por JavaScript, selectores que cambian, lazy loading, y diferencias sutiles entre navegadores.

**Productos objetivo:**

1. `Bicicleta rodado 29`
2. `iPhone 16 Pro Max`
3. `GeForce RTX 5090`

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

---

### Hit #7

Construya un **Dockerfile** que empaquete el scraper junto con Chrome, Firefox y los drivers, de modo que se pueda ejecutar con un único comando:

```bash
docker run --rm -v $(pwd)/output:/app/output ml-scraper:latest --browser firefox
```

Configure un **GitHub Actions workflow** (`.github/workflows/scrape.yml`) que:

1. Construya la imagen Docker.
2. Corra el scraper en headless contra Chrome y Firefox (jobs en paralelo, matriz).
3. Ejecute los tests del Hit #6.
4. Publique los JSON y screenshots como **artifacts** del workflow.
5. Falle si gitleaks detecta secrets hardcodeados.

---

### Hit #8 (Bonus)

Extienda el scraper con cualquiera (o varias) de las siguientes capacidades:

1. **Paginación**: traer los primeros 30 resultados en lugar de 10, navegando hasta 3 páginas.
2. **Comparación de precios**: para cada producto, calcular precio mínimo, máximo, mediana y desvío estándar entre los resultados extraídos. Imprimir tabla resumen.
3. **Histórico**: guardar los resultados en una base de datos liviana (SQLite) con timestamp, para detectar cambios de precio si el scraper se ejecuta periódicamente.
4. **Reporte HTML**: generar una página estática (con GitHub Pages publicada por el pipeline) que muestre los resultados de la última corrida en una tabla navegable.
5. **Page Object Model**: refactorizar el scraper para separar el código de navegación (`SearchPage`, `ResultsPage`) del código de extracción y de los tests.

---

## Criterios de evaluación

| Criterio | Peso |
|----------|------|
| Funciona en Chrome **y** Firefox sin cambios de código (solo config) | 20 % |
| Filtros aplicados correctamente vía DOM (nuevo + tienda oficial) | 15 % |
| Datos extraídos completos, bien tipados y serializados | 15 % |
| Manejo robusto de errores (selectores faltantes, timeouts, retries) | 15 % |
| Tests automatizados cubriendo el flujo crítico | 10 % |
| Pipeline CI/CD funcional con matriz de browsers | 10 % |
| Calidad de código (waits explícitos, selectores en módulo aparte, sin sleeps) | 10 % |
| Informe y video explicativo | 5 % |

---

## Referencias y Bibliografía

- **[SEL]** Selenium Documentation. <https://www.selenium.dev/documentation/>
- **[W3C-WD]** W3C WebDriver Specification. <https://www.w3.org/TR/webdriver2/>
- **[POM]** Page Object Model — Selenium Wiki. <https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/>
- **[CSS-SEL]** MDN — CSS Selectors. <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors>
- **[XPATH]** MDN — XPath. <https://developer.mozilla.org/en-US/docs/Web/XPath>
- **[GH-ACTIONS]** GitHub Actions Documentation. <https://docs.github.com/en/actions>
- **[GITLEAKS]** gitleaks — Protect and discover secrets using Gitleaks. <https://github.com/gitleaks/gitleaks>
- **[ROBOTS]** The Robots Exclusion Protocol. <https://www.rfc-editor.org/rfc/rfc9309>
- **[ML]** MercadoLibre Argentina. <https://www.mercadolibre.com.ar>
