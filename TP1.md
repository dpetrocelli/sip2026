# Trabajo Práctico Nº 1 — Parte 1

## Automatización Web con Selenium — Pruebas E2E multi-browser sobre MercadoLibre

**Fecha de Entrega: 25/04/2026**

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

## Criterios de evaluación — Parte 1

| Criterio | Peso |
|----------|------|
| Hit #1 — setup, navegación, búsqueda y lectura de títulos | 15 % |
| Hit #2 — Browser Factory funcionando contra Chrome **y** Firefox sin cambios de código | 25 % |
| Hit #3 — filtros aplicados correctamente vía DOM (nuevo + tienda oficial) y screenshot | 30 % |
| Calidad de código (waits explícitos, selectores en módulo aparte, sin `time.sleep`) | 15 % |
| README, informe y video explicativo | 10 % |
| Dockerfile básico (deseable, suma puntos) | 5 % |

---

## Referencias y Bibliografía

- **[SEL]** Selenium Documentation. <https://www.selenium.dev/documentation/>
- **[W3C-WD]** W3C WebDriver Specification. <https://www.w3.org/TR/webdriver2/>
- **[CSS-SEL]** MDN — CSS Selectors. <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors>
- **[XPATH]** MDN — XPath. <https://developer.mozilla.org/en-US/docs/Web/XPath>
- **[GITLEAKS]** gitleaks. <https://github.com/gitleaks/gitleaks>
- **[ROBOTS]** The Robots Exclusion Protocol. <https://www.rfc-editor.org/rfc/rfc9309>
- **[ML]** MercadoLibre Argentina. <https://www.mercadolibre.com.ar>
