# Devolución — ProxyTeam (correamiq + MiqueasC)

**Repo:** [correamiq/Testing-Selenium-ProxyTeam](https://github.com/correamiq/Testing-Selenium-ProxyTeam)
**Commit evaluado:** [`a3d97eb`](https://github.com/correamiq/Testing-Selenium-ProxyTeam/commit/a3d97ebbef96) (2026-04-25 17:24 UTC)
**Stack:** Python 3 + Selenium + pytest
**Próxima entrega:** Parte 2 — 02/05/2026. [Consigna](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html) · [TP 0 Prerrequisitos](https://dpetrocelli.github.io/sip2026/practica-0.html)
**Score final:** **68.7 / 100** (auto: 75 · manual: 62.5)

> Ranking: 4°. Buena base técnica pero hay 2 bugs serios que hacen que el código pase tests sin que los filtros funcionen realmente.

---

## Nota desglosada por criterio

| Criterio | Peso | Tu nota | Nota máx |
|---|---:|---:|---:|
| Hit #1 — setup, navegación, búsqueda, 5 títulos | 15 % | 14 | 15 |
| Hit #2 — Browser Factory (con bug `getoption`) | 25 % | 16 | 25 |
| Hit #3 — filtros DOM (test débil + solo Chrome) | 30 % | 16 | 30 |
| Calidad de código (waits, selectores) | 15 % | 11 | 15 |
| README + informe + video | 10 % | 5 | 10 |
| Dockerfile (deseable) | 5 % | 0 | 5 |
| Bonus `.gitignore` impecable + UA workaround descubierto | +6.7 | +6.7 | — |
| **Total** | **100 %** | **68.7** | **100** |

## Cumplimiento punto por punto de la consigna

### Hit #1 — Setup + búsqueda + 5 títulos
✅ **Cumplido**. **Detalle valioso que descubrieron**: el User-Agent custom evita que ML detecte headless y devuelva empty-state. Está bien aplicado en el `conftest.py`.

### Hit #2 — Browser Factory multi-browser
🟠 **Cumplido pero con bug**. El código es:

```python
getoption("--browser") or os.environ.get("BROWSER", "chrome")
```

**Bug**: como `--browser` ya tiene `default="chrome"` en el `addoption`, **`getoption()` siempre devuelve un valor truthy** → la rama `os.environ.get("BROWSER")` **NUNCA se evalúa**. La consigna pedía cadena CLI > env > default; ustedes implementaron CLI > default, ignorando env.

**Fix**: cambiá el default del `addoption` a `None` y resolvé manualmente:
```python
b = getoption("--browser") or os.environ.get("BROWSER", "chrome")
```

### Hit #3 — Filtros DOM + screenshot
🟠 **Acá está el bug más serio**. El test es:

```python
def test_filtros_aplicados(driver):
    safe_click(driver, ...)  # silencia TimeoutException
    safe_click(driver, ...)
    titles = ...
    assert len(titles) >= 3   # ← assert débil
```

**Problema**: `safe_click` silencia errores → si el filtro NO se aplica el test pasa igual. Y el assert `len >= 3` siempre va a ser True porque ML siempre tiene >3 resultados. **Resultado: el test pasa sin probar realmente que los filtros funcionen.**

**Fix sugerido**: validar que los **resultados estén filtrados** — por ejemplo contar elementos con badge "tienda oficial" después del filtro, o verificar que la URL incluye el parámetro de filtro aplicado, o hacer un screenshot diff antes/después.

🟡 **Screenshot solo de Chrome**, falta Firefox.

### Calidad de código (15%)
✅ Explicit waits con `WebDriverWait + expected_conditions` consistentemente.
🟡 **Selectores duplicados**: `li.ui-search-layout__item` aparece en 6 lugares de los tests. Centralizalo en un `selectors.py`.
🟡 README raíz: no hay.

### README + informe + video (10%)
🟠 READMEs por hit están bien, pero **falta README raíz** con integrantes + legajos. Sin video confirmado, sin informe consolidado, sin comparativa Chrome vs Firefox.

### Dockerfile (5% deseable)
❌ No entregaron.

### Requisitos generales
✅ **`.gitignore` correcto**, sin secrets, sin `__pycache__/` commiteado, sin `.venv` adentro. **Esto es lo más limpio del curso.**
❌ Sin CI workflow.
❌ Sin gitleaks.

---

## Para Parte 2

1. **🚨 Arreglar el bug del Hit #2** (CLI > env > default). Es 5 minutos pero invalida la consigna del Hit #2 si no se corrige.
2. **🚨 Fortalecer el assert del Hit #3** — el test actual pasa sin probar filtros. Sin esto el código de Parte 2 (Hit 4 - extracción JSON) se va a apoyar en filtros que no funcionan.
3. **README raíz** con integrantes (correamiq + MiqueasC + legajos).
4. **Centralizar selectores** en `selectors.py` (NOT `selectors` — ese nombre choca con stdlib de Python).
5. **Implementar Hit #4** con extracción JSON estructurada de los 3 productos.
6. **Dockerfile + GitHub Actions** con matriz Chrome/Firefox.

**Mensaje positivo**: el descubrimiento del UA custom para evitar el detect-headless de ML fue una buena observación que el resto del curso NO encontró. Si arreglan los 2 bugs (`--browser` y assert), suben fácil al podio.

---

## Tiempo estimado de arreglos pendientes

| Tarea | Estimado |
|---|---:|
| **🚨 Fix bug `--browser` resolution chain** (Hit #2) | 5 min |
| **🚨 Fortalecer assert del Hit #3** (validar filtros aplicados de verdad) | 30 min |
| README raíz + integrantes + IA + Chrome vs Firefox | 30 min |
| `selectors.py` (no `selectors`, choca con stdlib) | 30 min |
| Hit #4 (extracción JSON estructurada de los 3 productos) | 3-4 h |
| Hit #5 (retries + backoff + selectores centralizados) | 2 h |
| Hit #6 (tests + coverage ≥ 70 %) | 2 h |
| Hit #7 (Dockerfile + CI + pre-commit + gitleaks) | 3 h |
| Hit #8 (k8s) + TP 0 (cluster k3s) | 3 h |
| 3 ADRs | 30 min |

**Total Parte 2:** ~14-16 h. Tenés 6 días → ~2.5 h/día.

## Recursos cátedra para Parte 2

- [Implementación de referencia completa](https://github.com/dpetrocelli/sip2026/tree/main/reference) — Python 3.13 + Selenium + pytest, **el stack más cercano al suyo**. Estudien especialmente el `conftest.py` y `tests/test_browser_factory.py` para ver cómo arreglar el bug del Hit #2 con tests que lo prueben.
- [`tooling/compare.py`](https://github.com/dpetrocelli/sip2026/blob/main/reference/tooling/compare.py) — comparador automático. Después de arreglar los 2 bugs críticos, deberían subir bastante el score auto.
- [Sección "Auto-verificación previa a la entrega"](https://dpetrocelli.github.io/sip2026/practica-1-parte-2.html#auto-verificacion-previa-a-la-entrega).
