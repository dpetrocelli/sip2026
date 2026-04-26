# Trabajo Práctico Nº 1 — Parte 2

## Robustez, Tests, Docker y CI/CD sobre el scraper de MercadoLibre

**Fecha de Entrega: 02/05/2026**

**Pre-requisito:** Haber entregado la **Parte 1** (Hits #1–#4). Esta segunda parte continúa el mismo proyecto.

---

## Requisitos, consideraciones y formato de entrega

Aplican los mismos requisitos generales de la Parte 1, **más** los siguientes:

- **Pipeline de CI/CD obligatorio** (GitHub Actions). Debe correr el scraper en headless contra Chrome y Firefox y publicar los artefactos generados (JSON + screenshots).
- **Dockerfile obligatorio**. La solución debe poder ejecutarse íntegramente desde un contenedor sin necesidad de instalar drivers ni navegadores en la máquina host.
- **Tests automatizados obligatorios** (`pytest` / `JUnit` / `Jest`) corriendo en CI sobre matriz de browsers.
- Mantener las **buenas prácticas** ya exigidas en Parte 1: explicit waits, selectores en módulo aparte, logs estructurados, no commitear secrets, gitleaks en CI.

---

## Contenidos del programa relacionados

- Robustez en automatización: timeouts, retries, manejo de fallos parciales.
- Headless browsing y empaquetado en contenedores.
- Testing de software: integración, contratos de datos, schemas.
- Pipelines de CI/CD y matrices de ejecución.
- Patrones avanzados: Page Object Model.

---

## Práctica

En la **Parte 1** construyeron un scraper que extrae 10 resultados filtrados por producto, multi-browser, con datos estructurados en JSON. Funciona, pero es frágil: cualquier cambio en el DOM de MercadoLibre lo rompe, no hay forma de garantizar que el output sea válido sin abrir los archivos a mano, y no se puede correr en un servidor sin display gráfico.

En esta **Parte 2** vamos a llevarlo a calidad de producción: robustez ante fallos, modo headless, tests automatizados, empaquetado en Docker, y pipeline de CI/CD que ejecute todo con cada push.

Continuamos con los mismos productos:

1. `Bicicleta rodado 29`
2. `iPhone 16 Pro Max`
3. `GeForce RTX 5090`

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

## Criterios de evaluación — Parte 2

| Criterio | Peso |
|----------|------|
| Manejo robusto de errores (selectores faltantes, timeouts, retries con backoff) | 20 % |
| Tests automatizados cubriendo el flujo crítico, corriendo en CI | 20 % |
| Dockerfile funcional con Chrome + Firefox + drivers, multi-stage si aplica | 20 % |
| Pipeline CI/CD funcional con matriz de browsers y artifacts publicados | 20 % |
| Modo headless configurable y operativo | 10 % |
| Hit #8 (al menos uno de los bonus) | 10 % |

---

## Referencias y Bibliografía

- **[SEL]** Selenium Documentation. <https://www.selenium.dev/documentation/>
- **[POM]** Page Object Model — Selenium Wiki. <https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/>
- **[GH-ACTIONS]** GitHub Actions Documentation. <https://docs.github.com/en/actions>
- **[DOCKER]** Docker — Best practices for writing Dockerfiles. <https://docs.docker.com/develop/develop-images/dockerfile_best-practices/>
- **[GITLEAKS]** gitleaks. <https://github.com/gitleaks/gitleaks>
- **[ML]** MercadoLibre Argentina. <https://www.mercadolibre.com.ar>
