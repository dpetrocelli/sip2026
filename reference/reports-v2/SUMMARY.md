# Evaluación Consolidada v2 — TP 1 Parte 1 (Hits 1-3)

**Fecha:** 2026-04-26
**Entrega:** 25/04/2026
**Metodología:** doble análisis — pasada automática con `tooling/compare.py` + revisión manual por agentes especializados.

> Esta v2 incorpora el análisis automático contra el **golden output** de la cátedra (`expected-output/`). El score automatizado evalúa estructura, presencia de patrones y schema del JSON. El score manual de la v1 (en `evaluator/reports/`) profundiza en bugs sutiles, anti-patterns ocultos y revisión cualitativa.

## Ranking final (combinado)

| # | Equipo | Stack | Auto v2 | Manual v1 | Final |
|---|--------|-------|--------:|----------:|------:|
| 1 | **Systeam** (Casal) | Node 20 + Jest | 82 | 86.3 | **84** |
| 2 | **Contardi** | Python 3 | 90 | 75 | **82.5** |
| 3 | **G-ONE** (GonzaEC) | Java 17 + Maven | 90 | 73.9 | **82** |
| 4 | **ProxyTeam** (correamiq) | Python 3 + pytest | 75 | 62.5 | **68.7** |

> **Final** = promedio simple de auto y manual. Las diferencias reflejan que el auto premia presencia estructural mientras que el manual castiga bugs sutiles (assert débil, target/ commiteado, README vacío, etc.). Ningún ranking solo es justo — la combinación lo es.

## Detalle por equipo (links a reportes individuales)

### 🥇 Systeam — Casal · 84/100

- [Reporte automático v2](SIP-Selenium-Systeam.md)
- [Reporte manual v1](../../../../evaluator/reports/SIP-Selenium-Systeam.md)

**Por qué auto le da 82**: pierde 13 pts en "Calidad de código" porque el comparator detectó `setTimeout(600)` (1 sleep) y porque el regex de "selectores centralizados" no matcheó la estructura JS de Systeam (carpeta `pages/` con `FiltersPage.js` en lugar de un `selectors.js` plano). **Caso falso negativo del auto** — Systeam SÍ tiene selectores centralizados en POM.

**Por qué manual le da 86.3**: validó que el POM es la organización correcta para el stack JS. Penalizó solo el `setTimeout(600)` real.

### 🥈 Contardi · 82.5/100

- [Reporte automático v2](TP1-Selenium.md)
- [Reporte manual v1](../../../../evaluator/reports/TP1-Selenium.md)

**Por qué auto le da 90**: cero `time.sleep`, hits 1-3 presentes con README, browser factory detectada. El auto NO ve los anti-patterns sutiles.

**Por qué manual le da 75**: README raíz vacío ("# TP1-Selenium\nTP1 Selenium" y nada más), `__pycache__/` commiteado, typo en `requeriments.txt`, selectores hardcodeados inline (no centralizados aunque el módulo "exista" como concepto), `print()` en lugar de logging. El auto no es lo suficientemente fino para detectar la mitad de esto.

### 🥉 G-ONE — GonzaEC · 82/100

- [Reporte automático v2](TP1-SIP.md)
- [Reporte manual v1](../../../../evaluator/reports/TP1-SIP.md)

**Por qué auto le da 90**: el código Java está bien estructurado, hay browser factory, READMEs por hit, filtros DOM. El comparator NO compila — solo lee.

**Por qué manual le da 73.9**: **`target/` commiteado** (4-5 commits de `.class` archivos en el repo, falta `.gitignore`), sin tests JUnit, screenshot solo de Chrome, `System.out.println` en lugar de SLF4J. El auto no hace `git ls-files` por categorías, así que no detecta `target/`.

### Cuarto — ProxyTeam — correamiq · 68.7/100

- [Reporte automático v2](Testing-Selenium-ProxyTeam.md)
- [Reporte manual v1](../../../../evaluator/reports/Testing-Selenium-ProxyTeam.md)

**Por qué auto le da 75**: hits presentes, explicit waits, .gitignore correcto, pytest tests. Browser Factory detectada parcialmente (le dio 10/25 — el regex no matcheó del todo).

**Por qué manual le da 62.5**: **Hit #3 con assert débil** (`safe_click` silencia `TimeoutException`, assert solo valida `len >= 3` → tests pasan aunque ningún filtro funcione), **bug en Hit #2** (`getoption("--browser") or env` → env nunca se evalúa porque `--browser` siempre tiene default), screenshots solo de Chrome. El auto no puede detectar fallas semánticas en tests.

## Resumen de la rúbrica

```
Hit 1 — setup + búsqueda            15 %
Hit 2 — Browser Factory             25 %
Hit 3 — filtros DOM + screenshot    30 %
Calidad de código                   15 %
README/informe/video                10 %
Dockerfile (deseable)                5 %
                                  ─────
                                   100 %
```

Vivo en [`pyproject.toml`](../pyproject.toml) y validado por [`tooling/compare.py`](../tooling/compare.py).

## Limitaciones del análisis automático (gaps a tener en cuenta)

| Lo que `compare.py` SÍ detecta | Lo que NO detecta (requiere manual) |
|--------------------------------|--------------------------------------|
| Carpetas hit1/hit2/hit3 presentes | Calidad real del Browser Factory (¿maneja env vars correctamente?) |
| `time.sleep` / `setTimeout` (anti-pattern) | Asserts débiles que enmascaran fallos |
| Selectores en archivo separado | Si los selectores son frágiles (clases auto-generadas) |
| Schema JSON básico | Si el JSON refleja resultados reales o mock data |
| `.env` / `.pem` commiteados | Bugs en lógica de negocio (priorización env vs CLI) |
| Dockerfile presente | Si el Dockerfile es non-root, multi-stage, etc. |
| Tests presentes | Si los tests son significativos o solo `assert True` |

**Conclusión**: el `tooling/compare.py` es un **screen automatizado** para descartar entregas que no cumplan lo mínimo. La revisión manual sigue siendo necesaria para nota final.

## Cómo correr el comparator

```bash
# 1 alumno
python tooling/compare.py --student /path/al/repo --out reports-v2/<nombre>.md

# Todos los alumnos en un loop
for d in evaluator/repos/*/; do
  python tooling/compare.py --student "$d" --out "reports-v2/$(basename $d).md"
done
```
