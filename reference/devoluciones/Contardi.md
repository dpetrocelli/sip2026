# Devolución — Contardi (Gustavo Contardi)

**Repo:** [GustavoContardi/TP1-Selenium](https://github.com/GustavoContardi/TP1-Selenium)
**Stack:** Python 3 + Selenium
**Score final:** **82.5 / 100** (auto: 90 · manual: 75)

> Ranking: 🥈 2°. Código limpio, anti-patterns ausentes, pero el envoltorio (README raíz, video, .gitignore) flojea.

---

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
