# Devolución — Systeam (Ulises Casal)

**Repo:** [UlisesCasal/SIP-Selenium-Systeam](https://github.com/UlisesCasal/SIP-Selenium-Systeam)
**Stack:** Node.js 20 + Selenium WebDriver 4.27 + Jest 29 + winston
**Score final:** **84 / 100** (auto: 82 · manual: 86.3)

> Ranking: 🥇 1° — la entrega más sólida del curso. Felicitaciones por el nivel.

---

## Cumplimiento punto por punto de la consigna

### Hit #1 — Setup + búsqueda + 5 títulos por consola
**Pedido**: Selenium configurado, navegar a ML, búsqueda por keyword, imprimir 5 títulos. Explicit waits, **prohibido** `setTimeout`/`sleep` como mecanismo de sincronización.

✅ **Cumplido**. Browser arranca, búsqueda funciona, 5 títulos por stdout. Explicit waits con `WebDriverWait` correctamente.

### Hit #2 — Browser Factory multi-browser
**Pedido**: clase/función que toma `chrome`/`firefox` por env var/CLI, funciona idéntico en ambos. Documentar diferencias en informe.

✅ **Cumplido y mejorado**. Refactorizaron con `BrowserOptions` como **value object testeable** (esto es deeper de lo que la consigna pedía). Resolución argumento → env → default funciona. Labels Kubernetes-grade.

### Hit #3 — Filtros vía DOM (nuevo + tienda oficial) + screenshot
**Pedido**: clicks reales sobre los filtros (no modificar URL), screenshot a `screenshots/<producto>_<browser>.png`.

✅ **Cumplido**. Filtros vía clicks reales, no modificación de URL. Screenshots presentes.

### Calidad de código (15%)
**Pedido**: explicit waits, selectores en módulo aparte, sin `time.sleep`/`setTimeout`.

🟡 **Casi perfecto, 1 punto de fricción**: `HIT3/src/pages/FiltersPage.js:274` tiene un `setTimeout(600)` para esperar el dropdown de Andes. Es el ÚNICO sleep duro en todo el código y es un workaround para una transición CSS — pero técnicamente es la práctica que la consigna prohibe. **Para Parte 2: reemplazar por `until(EC.attributeContains(...))`** que detecte el estado abierto del dropdown.

Selectores: ✅ centralizados con multi-fallback (esto está mejor que la consigna pedía).

### README, informe y video explicativo (10%)
**Pedido**: README claros por hit con instrucciones, decisiones de diseño, comparativa Chrome vs Firefox, herramientas de IA usadas.

🟡 **Falta README raíz** que liste integrantes (lo único que tiene es los READMEs por hit, que están bien). Video y comparativa Chrome vs Firefox — verificar si están en el repo o solo planeados.

### Dockerfile (5% deseable)
❌ **No entregaron Dockerfile**. Pierden los 5 pts de bonus de Parte 1, **pero en Parte 2 es obligatorio**.

---

## Lo que más rescato del trabajo

1. **Único equipo con CI/CD funcional**: GitHub Actions con `gitleaks` + matriz Chrome/Firefox + GitHub Pages publicando results. Esto es scope de Parte 2 — lo trajeron a Parte 1.
2. **15/15 unit tests pasan** localmente. Browser Factory totalmente testeable sin browser real (mocks bien aplicados).
3. **Logging estructurado con winston a archivo** — el resto del curso usa `console.log`/`print`.

---

## Para Parte 2 (entrega 02/05/2026)

1. **Implementar Hit #4** (extracción JSON estructurada de los 3 productos). Es el punto de partida de toda Parte 2.
2. **Sacar el `setTimeout(600)`** de `FiltersPage.js:274`. Es el único antipattern que les queda.
3. **README raíz con tabla de integrantes**. G-ONE lo hizo y es el ejemplo a seguir.
4. **Dockerfile multi-stage** — ya tenés CI armado, ahora le sumás Docker para que la imagen se publique como artifact.
5. **Compartir código entre HIT1/HIT2/HIT3** — hay duplicación. Considerá `npm workspaces` o un paquete `core/` compartido.

**Bonus**: tu CI tiene componentes que el resto del curso no entregó. Para Parte 2 podés crecerlo con Helm chart (k8s del Hit #8) y Page Object Model formalizado.
