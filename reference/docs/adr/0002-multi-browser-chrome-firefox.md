# 0002 — Soportar Chrome y Firefox simultáneamente desde el Hit #2

- **Date:** 2026-04-26
- **Status:** Accepted
- **Deciders:** Cátedra SIP 2026

## Contexto

El scraper tiene que correr en CI y eventualmente en un cluster Kubernetes (Hit #8). Una decisión inicial razonable parecería ser "soportemos un solo browser, lo simplificamos". El problema con esa lógica es que en producción real **nunca controlamos qué motor de browser corre el cliente**: un script que solo funciona en Chromium es frágil por diseño, porque depende implícitamente de quirks del motor Blink (event loop, timing de eventos, parsing de CSS, comportamiento de `<details>`, etc.) que no son parte del estándar W3C WebDriver.

Las opciones evaluadas:

1. **Chrome only** — más simple, CI más rápido, una sola dependencia de driver. Pero el código resultante puede tener supuestos no portables que recién se descubren cuando llega un cliente con Firefox/Safari.
2. **Chrome + Firefox** — fuerza al código a usar selectores y waits que funcionen en ambos motores (Blink y Gecko), valida la decisión del ADR 0001 (Selenium W3C-compliant), duplica el tiempo de CI y la complejidad del Dockerfile.
3. **Chrome + Firefox + WebKit** — cobertura ideal, pero WebKit en Linux requiere Playwright (no Selenium), y entra en conflicto con ADR 0001. Descartado.

El costo concreto de soportar dos browsers en CI es ~2x el tiempo de ejecución del job de tests (matriz de GitHub Actions con `fail-fast: false`). En la práctica son ~3-5 minutos extra por push, aceptables para un proyecto educativo y para la inmensa mayoría de proyectos reales.

## Decisión

Soportamos **Chrome (Chromium) y Firefox (Gecko)** simultáneamente desde el Hit #2 en adelante, vía un **Browser Factory** (`get_driver(browser: str)`) que abstrae las diferencias de inicialización. La selección se hace por variable de entorno `BROWSER=chrome|firefox` y la matriz de CI ejecuta ambos en paralelo.

## Consecuencias

- **Más fácil:** el código resultante es genuinamente portable; los selectores deben ser estables W3C (nada de `:-webkit-*` ni hacks específicos de Blink); valida que las decisiones de waits y timeouts no dependan de quirks de un motor.
- **Más difícil:** Browser Factory necesario (no más; es ~30 líneas de código); los timeouts deben ajustarse al motor más lento (Firefox suele ser ~30 % más lento que Chrome en first-contentful-paint sobre páginas pesadas como MercadoLibre); la imagen de Docker tiene que incluir ambos browsers + ambos drivers, lo que infla la imagen final.
- **Costo de CI:** la matriz duplica el tiempo de ejecución. Mitigado con `fail-fast: false` para que el feedback de un browser no bloquee el del otro, y con cache de pip/npm para que solo el browser-run sea el costo extra real.
- **Riesgo (drift entre browsers):** un test puede pasar en Chrome y fallar en Firefox por un selector específico. Esto no es un bug, es **exactamente el valor** de tener la matriz: detectarlo en CI antes que en producción.

## Referencias

- WebDriver BiDi (próximo estándar de control de browsers, soportado por ambos motores): <https://w3c.github.io/webdriver-bidi/>
- chromedriver: <https://chromedriver.chromium.org/>
- geckodriver: <https://github.com/mozilla/geckodriver>
- "Cross-Browser Testing in Selenium" — Selenium Wiki: <https://www.selenium.dev/documentation/test_practices/encouraged/cross_browser_testing/>
- ADR 0001 (Selenium) — esta decisión depende de aquélla y, de hecho, valida su elección.
