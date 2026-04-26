# Devolución — G-ONE (5 integrantes)

**Repo:** [GonzaEC/TP1-SIP](https://github.com/GonzaEC/TP1-SIP)
**Commit evaluado:** [`9f55499`](https://github.com/GonzaEC/TP1-SIP/commit/9f5549970b3b) (2026-04-25 17:30 UTC)
**Stack:** Java 17 + Selenium 4.20 + Maven
**Integrantes:** Roberto Soto · Nicolas Romero · Cristian Tomás Anito · Rocco Buzzo Marcelo · Gonzalo Echeverria Crenna
**Próxima entrega:** Parte 2 — 02/05/2026. [Consigna](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html) · [TP 0 Prerrequisitos](https://dpetrocelli.github.io/sip2026/practica-0.html)
**Score final:** **82 / 100** (auto: 90 · manual: 73.9)

> Ranking: 🥉 3°. Documentación impecable, pero hay un tema operativo grave: `target/` commiteado.

---

## Nota desglosada por criterio

| Criterio | Peso | Tu nota | Nota máx |
|---|---:|---:|---:|
| Hit #1 — setup, navegación, búsqueda, 5 títulos | 15 % | 15 | 15 |
| Hit #2 — Browser Factory Chrome+Firefox | 25 % | 25 | 25 |
| Hit #3 — filtros DOM + screenshot (solo Chrome) | 30 % | 24 | 30 |
| Calidad de código (waits, selectores, sin sleep) | 15 % | 12 | 15 |
| README + informe + video | 10 % | 8 | 10 |
| Dockerfile (deseable) | 5 % | 0 | 5 |
| **Penalización** `target/` commiteado | -2 | -2 | — |
| **Total** | **100 %** | **82** | **100** |

## Cumplimiento punto por punto de la consigna

### Hit #1 — Setup + búsqueda + 5 títulos
✅ **Cumplido**. WebDriverWait correctamente, navegación + búsqueda + lectura de títulos.

### Hit #2 — Browser Factory multi-browser
✅ **Cumplido y bien diseñado**. Clase Factory con cadena `argumento → -Dbrowser → $BROWSER → default`. Limpia, idiomática Java.

### Hit #3 — Filtros DOM + screenshot
✅ **Cumplido**. JS click + scrollIntoView para evitar `ElementClickInterceptedException` (decisión correcta y documentada). Screenshot capturado vía `TakesScreenshot`.

🟡 **Solo Chrome**, falta Firefox. La consigna pide validar **ambos** browsers.

### Calidad de código (15%)
✅ **Cero `Thread.sleep`** verificado por grep. Excellent.
✅ Explicit waits granulares + manejo de `TimeoutException` por filtro.
🟡 **Selectores XPath de filtros se construyen inline en `aplicarFiltro()`** — mismo problema que Contardi: faltan centralizados en una clase `Locators` o `PageObjects`.
🟡 **`System.out.println` en lugar de SLF4J**. La consigna pide logs estructurados.

### README + informe + video (10%)
✅ **MEJOR DEL CURSO en este criterio**: README raíz con tabla de integrantes + legajos. READMEs por hit con tabla comparativa Chrome vs Firefox y justificación de decisiones (por qué JS click, por qué cerrar banner cookies, texto exacto de los filtros). Esto es lo que la consigna pidió y lo cumplieron mejor que nadie.

🟡 **Falta video**. Confirmar si está subido al repo o solo planeado.

### Dockerfile (5% deseable)
❌ No entregaron.

### Requisitos generales — **PROBLEMA OPERATIVO IMPORTANTE**
- ❌ **`target/` commiteado al repo** — verificado con `git ls-files`. Hay 4-5 commits con `.class` files compilados. **Esto es un blooper grande** — agrega ruido al diff, pesa MB innecesarios, y revela que falta `.gitignore`.
- ❌ Sin `.gitignore` en absoluto.
- ❌ Sin `src/test/java/` — la consigna pide pruebas automatizadas.
- ❌ Sin CI workflow.

---

## Para Parte 2

1. **🚨 URGENTE**: agregar `.gitignore` con `target/`, `*.class`, `.idea/`, `.vscode/` y borrar `target/` del history (al menos del HEAD: `git rm -r --cached target/ && git commit`). Si querés limpieza total del history podés usar `git-filter-repo` pero no es obligatorio.
2. **Centralizar selectores** en una clase `Locators.java` o `PageObjects/` siguiendo Page Object Model.
3. **Migrar `System.out.println` → SLF4J** (`Logger logger = LoggerFactory.getLogger(...)`) con appenders a archivo.
4. **JUnit 5 tests** en `src/test/java/` con cobertura ≥ 70 % medida por `jacoco-maven-plugin`.
5. **Dockerfile multi-stage** con Maven build + runtime layer (JRE 17 + browsers + drivers).
6. **GitHub Actions** matriz Chrome/Firefox.
7. **Implementar Hit #4** + screenshot también de Firefox.

**Lo bueno**: como tienen los mejores READMEs del curso, llegar a la calidad de Systeam (que es 1°) está al alcance — solo necesitan sumar tooling.

---

## Tiempo estimado de arreglos pendientes

| Tarea | Estimado |
|---|---:|
| `.gitignore` + limpiar `target/` del HEAD | 15 min |
| `Locators.java` con todos los XPath movidos | 1 h |
| Migrar `System.out.println` → SLF4J + Logback | 45 min |
| Hit #4 (extracción JSON estructurada de los 3 productos) | 4-5 h (Java es más verboso) |
| Hit #5 (retries con backoff — usá `failsafe-rs` o `resilience4j`) | 2 h |
| Hit #6 (JUnit 5 + JaCoCo coverage ≥ 70 %) | 2-3 h |
| Hit #7 (Dockerfile multi-stage Maven + JRE + browsers) | 2 h |
| Hit #8 (k8s) + TP 0 (cluster k3s) | 3 h |
| 3 ADRs | 30 min |

**Total Parte 2:** ~16-18 h. Con 5 personas son ~3.5 h por integrante.

## Recursos cátedra para Parte 2

- [Implementación de referencia completa (Python)](https://github.com/dpetrocelli/sip2026/tree/main/reference) — está en Python pero la **estructura** (separación por hits, ADRs, manifests k8s, CI workflow) es 1:1 traducible a Java.
- [`tooling/compare.py`](https://github.com/dpetrocelli/sip2026/blob/main/reference/tooling/compare.py) — funciona contra cualquier lenguaje (les dio 90/100 auto en Parte 1).
- [Sección "Auto-verificación previa a la entrega"](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html#auto-verificacion-previa-a-la-entrega) — incluye comandos Maven equivalentes (`mvn verify`, `mvn spotless:check`, etc.).
