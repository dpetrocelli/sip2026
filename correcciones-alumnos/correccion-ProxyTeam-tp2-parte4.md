# Corrección TP2 — Parte 4: Cierre — Comparativa, decisiones arquitectónicas y ADR magisterial

**Grupo:** Proxy Team
**Integrantes:**
- Ponti, Mateo Daniel
- Scialchi, Luciano Agustin
- Romero Monteagudo, Valentín Joel
- Cacciatore, Bautista
- Correa, Miqueas
**Repo GitHub:** https://github.com/correamiq/Testing-Selenium-ProxyTeam
**Fecha de defensa oral:** _______________________________________________
**Fecha de corrección:** 2026-05-09
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Partes 1, 2 y 3 entregadas y aprobadas (≥ 60/100 cada una) | ✅ OK | P1: 8.1, P2: 8.0, P3: 9.5 |
| B2 | Los 3 stacks corriendo el día de la defensa | ☐ OK / ☐ FALLA | Verificar en defensa |
| B3 | Existe `docs/adr/0012-stack-de-observabilidad-final.md` | ✅ OK | Archivo presente |
| B4 | ADR `0012` tiene ≥ 1500 palabras (contar antes de corregir) | ⛔ **FALLA** | **~1,100 palabras medidas — por debajo del mínimo** |

**Palabras contadas en ADR `0012`:** ~1,100 palabras (dos conteos independientes: 1,026 prosa + front-matter y 1,115 total con encabezados — ambos por debajo de 1,500)

**¿Pasa verificación bloqueante?** ⛔ **NO** — nota = **0**, fin de corrección

---

## CORRECCIÓN DETENIDA POR BLOQUEANTE B4

El archivo `docs/adr/0012-stack-de-observabilidad-final.md` existe en el repositorio y tiene las 8 secciones requeridas. Sin embargo, el conteo de palabras no alcanza el mínimo bloqueante de 1,500 palabras:

- Conteo de prosa (sin front-matter, sin encabezados markdown): **~1,026 palabras**
- Conteo total (incluyendo encabezados y front-matter): **~1,115 palabras**
- Mínimo requerido: **1,500 palabras**

El ADR tiene buena estructura y, si alcanzara el mínimo de palabras, la nota proyectada sería alta (ver sección de devolución). El problema es exclusivamente de extensión — las secciones están presentes pero son muy escuetas.

---

## NOTA FINAL TP2 PARTE 4: **0 / 10**

---

## Devolución General

**Evaluación proyectada si se alcanza el mínimo de 1,500 palabras:**

```
Las 8 secciones están presentes. Si el ADR se expande a ≥ 1,500 palabras con el
contenido que ya existe + las adiciones que se señalan abajo, la nota proyectada
sería aproximadamente:
  Hit #1 (mediciones):     12/15  — measurements.md presente con M1-M5 pero
                                     algunos timestamps aproximados
  Hit #2 (decision matrix): 15/15 — 5×5 completa con veredictos y caveats
  Hit #3 (ADR 0012):        49/50 — estructura excelente, solo extensión insuficiente
  Hit #4 (vendor-lockin):   14/15 — ensayo sólido, cierre honesto sobre OTel
  Defensa oral:              5/5  — a definir en defensa
  TOTAL proyectado:         ~95/100 (9.5/10) pendiente defensa
```

**Lo que hay que agregar al ADR 0012 para superar 1,500 palabras:**

```
Las secciones más escuetas que pueden expandirse sin comprometer la coherencia:

§2 Alternativas consideradas (~400-500 palabras requeridas):
  — Datadog y Splunk están mencionados brevemente (~2 líneas cada uno).
    Expandir con: TCO estimado, por qué no aplican al contexto del §1,
    qué funcionalidad específica les falta o sobra.

§4 Trade-offs aceptados (~200-300 palabras requeridas):
  — Tiene 2 trade-offs. Agregar al menos uno más en formato
    "renunciamos a X porque Y, mitigación: Z". Por ejemplo:
    "renunciamos a la UI de Kibana para logs del día a día porque
     Grafana cubre ese caso con los datasources ya configurados,
     mitigación: mantener Kibana disponible para búsqueda full-text
     en incidentes que requieran búsqueda no estructurada."

§5 Evidencia empírica (~100-200 palabras requeridas):
  — Cita las mediciones de measurements.md pero sin los números exactos
    en el cuerpo del texto. Expandir citando al menos 3 valores concretos:
    "la RAM de ES (M1: X Mi) vs Loki (Y Mi)" directamente en el párrafo.

§6 Plan de evolución (~200-300 palabras requeridas):
  — Los horizontes 6/12/24 meses son bullets concisos. Expandir cada
    horizonte con: qué métrica o evento dispara la acción, cuál es
    el riesgo si no se actúa, y quién es responsable del trigger.
```

**Contexto para el grupo:**
```
El ADR 0012 tiene contenido de calidad — estructura correcta, veredicto claro,
trade-offs honestos. El problema es exclusivamente de extensión: las secciones
necesitan ~400 palabras adicionales distribuidas en §2, §4, §5 y §6.

Las Partes 1, 2 y 3 están aprobadas (P1: 8.1, P2: 8.0, P3: 9.5). Si entregan
el ADR 0012 expandido antes de la fecha de defensa, se reabre la corrección
de esta parte y la nota proyectada es 9.5/10.

Referencia: el mínimo de 1,500 palabras equivale a aproximadamente 3 páginas
A4 en fuente 11pt — el ADR actual tiene ~2 páginas. Agregar 1 página de análisis
en las secciones §2 y §6 alcanza el mínimo.
```
