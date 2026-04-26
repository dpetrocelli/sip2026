# 0001 — Usar Selenium WebDriver y no Playwright/Puppeteer/Cypress

- **Date:** 2026-04-26
- **Status:** Accepted
- **Deciders:** Cátedra SIP 2026

## Contexto

El TP exige automatizar un browser para scrapear MercadoLibre desde código, soportando los 3 productos definidos en el enunciado (bicicleta rodado 29, iPhone 16 Pro Max, GeForce RTX 5090). Las herramientas razonables del mercado, en abril de 2026, son cuatro:

- **Selenium WebDriver 4.x** — implementación de referencia del estándar W3C WebDriver, con bindings oficiales para Python/Java/JavaScript/Ruby/C#. Drivers nativos para Chrome, Firefox, Edge y Safari. Es la herramienta más usada en QA empresarial y la más demandada en búsquedas laborales del rubro testing/automation.
- **Playwright** — más rápido, mejor DX, multi-browser nativo (Chromium/WebKit/Gecko), context isolation incorporada, auto-wait. Alternativa moderna y técnicamente superior en muchos aspectos.
- **Puppeteer** — atado a Chromium, descartado de entrada porque la consigna del TP exige multi-browser (ver ADR 0002).
- **Cypress** — diseñado para E2E de aplicaciones propias, no para scraping de sitios de terceros. Limitaciones de cross-origin y de control del browser que lo vuelven inadecuado para este caso.

Hay un trade-off real: Playwright es objetivamente más cómodo y más rápido. Pero el TP es una **herramienta de aprendizaje**, no un proyecto de producción a optimizar. La consigna pide explícitamente Selenium porque es la herramienta canónica del rubro y porque trabajar con su API verbosa fuerza al alumno a entender los conceptos subyacentes (waits explícitos, manejo de stale elements, By locators) en lugar de que la abstracción los oculte.

## Decisión

Usamos **Selenium 4.x** con los bindings oficiales de Python, contra `chromedriver` y `geckodriver` instalados localmente o vía contenedor.

## Consecuencias

- **Más fácil:** estándar W3C WebDriver garantiza portabilidad entre browsers; ecosistema enorme con respuestas en StackOverflow para virtualmente cualquier problema; bindings en 5 lenguajes permite que el aprendizaje sea transferible más allá de Python; la herramienta más usada en entrevistas técnicas de QA.
- **Más difícil:** la API es más verbosa que Playwright (waits explícitos manuales en vez de auto-wait); no hay context isolation nativo entre tests; los scripts son más frágiles ante cambios del DOM porque no hay locators auto-healing.
- **Riesgo (selectores frágiles):** mitigado en el Hit #5 mediante centralización de selectores en un módulo aparte (`selectors.py`) con nombres semánticos, y con un mecanismo de retries con backoff ante fallos transitorios. Un cambio de DOM en MercadoLibre se arregla en un solo archivo en lugar de propagarse.
- **Riesgo (drivers desalineados):** mitigado usando Selenium Manager (incluido en Selenium 4.6+), que descarga el driver compatible con la versión del browser instalado automáticamente.

## Referencias

- W3C WebDriver Specification: <https://www.w3.org/TR/webdriver2/>
- Selenium Documentation: <https://www.selenium.dev/documentation/>
- Selenium Manager: <https://www.selenium.dev/documentation/selenium_manager/>
- Comparativa Selenium vs Playwright (BrowserStack, 2025): <https://www.browserstack.com/guide/playwright-vs-selenium>
- ADR 0002 (multi-browser) — esta decisión es prerrequisito de aquélla.
