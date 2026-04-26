# Devolución — Contardi (Gustavo Contardi)

**Repo:** [GustavoContardi/TP1-Selenium](https://github.com/GustavoContardi/TP1-Selenium)
**Commit evaluado:** [`8221268`](https://github.com/GustavoContardi/TP1-Selenium/commit/8221268f753f) (2026-04-25 17:04 UTC)
**Stack:** Python 3 + Selenium
**Próxima entrega:** Parte 2 — 02/05/2026. [Consigna](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html) · [TP 0 Prerrequisitos](https://dpetrocelli.github.io/sip2026/practica-0.html)
**Score final:** **82.5 / 100** (auto: 90 · manual: 75)

> Ranking: 🥈 2°. Código limpio, anti-patterns ausentes, pero el envoltorio (README raíz, video, .gitignore) flojea.

---

## Nota desglosada por criterio

| Criterio | Peso | Tu nota | Nota máx |
|---|---:|---:|---:|
| Hit #1 — setup, navegación, búsqueda, 5 títulos | 15 % | 15 | 15 |
| Hit #2 — Browser Factory Chrome+Firefox | 25 % | 25 | 25 |
| Hit #3 — filtros DOM + screenshot | 30 % | 28 | 30 |
| Calidad de código (waits, selectores, sin sleep) | 15 % | 11.5 | 15 |
| README + informe + video | 10 % | 3 | 10 |
| Dockerfile (deseable) | 5 % | 0 | 5 |
| **Total** | **100 %** | **82.5** | **100** |

## Cumplimiento punto por punto de la consigna

### Hit #1 — Setup + búsqueda + 5 títulos
✅ **Cumplido**. Funciona contra ML, explicit waits aplicados.

### Hit #2 — Browser Factory multi-browser
✅ **Cumplido**. `browser_factory.py` con cadena de resolución CLI → env → default. Soporta chrome y firefox correctamente.

### Hit #3 — Filtros DOM + screenshot
✅ **Cumplido**. Filtros vía clicks reales (no URL), screenshot generada y commiteada. Smoke test verificado por la cátedra: corre 100% en Chrome headless.

### Calidad de código (15%)
✅ **Lo mejor de los 4 entregas en este criterio**: **cero `time.sleep`** en todo el código. El hit3 tiene anti-detection extra en `browser_factory.py` que va más allá de lo pedido.

🟡 **Pero**: selectores **hardcodeados inline** en cada función en lugar de en un `selectors.py` aparte. La consigna lo pide explícito ("Estructure los selectores en un módulo aparte" — Hit #5, pero el principio aplica).

🟡 **`print()` en lugar de `logging`** en todos los hits. La consigna pide "registros de actividades en consola y disco con niveles INFO/WARN/ERROR" — `print` no cumple eso.

### README + informe + video (10%)
🟠 **Acá perdés los puntos más concretos**.
- README raíz: `# TP1-Selenium\nTP1 Selenium` — vacío. **No hay tabla de integrantes con legajo, no hay link al video, no hay sección de herramientas de IA usadas, no hay comparativa Chrome vs Firefox.**
- READMEs por hit: estos sí están bien.

### Dockerfile (5% deseable)
❌ No entregaron.

### Requisitos generales (resto del 100%)
- ❌ **`__pycache__/` commiteado** — `.gitignore` mínimo (solo `/.venv`).
- ❌ Typo en `requeriments.txt` (es `requirements.txt`).
- ❌ Sin tests automatizados (la consigna lo pide).
- ❌ Sin CI workflow.

---

## Para Parte 2

1. **README raíz** con tabla de integrantes + link video + comparativa Chrome vs Firefox + herramientas de IA usadas. Tomá el de G-ONE como ejemplo.
2. **Crear `selectors.py`** moviendo todos los selectores hardcodeados ahí.
3. **Migrar `print` → `logging.getLogger(__name__)`** con nivel INFO/WARN/ERROR.
4. **`.gitignore` completo**: agregar `__pycache__/`, `output/`, `screenshots/`, `logs/`, `.env`.
5. **Renombrar** `requeriments.txt` → `requirements.txt` y verificar que el typo no rompió nada.
6. **Implementar Hit #4** + tests con coverage ≥ 70 % + Dockerfile + CI.

---

## Tiempo estimado de arreglos pendientes

| Tarea | Estimado |
|---|---:|
| README raíz completo (integrantes + decisiones + Chrome vs Firefox + IA) | 30 min |
| `selectors.py` con todos los selectores movidos | 45 min |
| Migrar `print` → `logging` (todos los archivos) | 30 min |
| `.gitignore` + renombrar `requeriments.txt` | 10 min |
| Hit #4 (extracción JSON estructurada de los 3 productos) | 3-4 h |
| Hit #5 (retries + backoff + selectores centralizados — ya parte ahí) | 2 h |
| Hit #6 (tests + coverage ≥ 70 %) | 2 h |
| Hit #7 (Dockerfile + CI + pre-commit) | 3 h |
| Hit #8 (k8s) + TP 0 (cluster k3s) | 3 h |
| 3 ADRs | 30 min |

**Total Parte 2:** ~14-16 h. Tenés 6 días → ~2.5 h/día.

## Recursos cátedra para Parte 2

- [Implementación de referencia completa](https://github.com/dpetrocelli/sip2026/tree/main/reference) — Python 3.13 + Selenium, así que la podés seguir bastante de cerca como estructura.
- [`tooling/compare.py`](https://github.com/dpetrocelli/sip2026/blob/main/reference/tooling/compare.py) — comparador automático que ya pasó tu repo a 90/100 auto. Volvé a correrlo sobre Parte 2 antes de entregar.
- [Sección "Auto-verificación previa a la entrega"](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html#auto-verificacion-previa-a-la-entrega).
