# Corrección TP2 — Parte 4: Cierre — Comparativa, decisiones arquitectónicas y ADR magisterial

**Grupo:** CFZ++
**Integrantes:**
- Contardi, Gustavo
- _______________________________________________
- _______________________________________________
- _______________________________________________
- _______________________________________________
**Repo GitHub:** https://github.com/GustavoContardi/TP1-Selenium (TP2 en subcarpeta `/TP2/`)
**Fecha de defensa oral:** _______________________________________________
**Fecha de corrección:** 2026-05-09
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Partes 1, 2 y 3 entregadas y aprobadas (≥ 60/100 cada una) | ⛔ **FALLA** | P1: 7.9 ✓, P2: 8.6 ✓, **P3: 0 (no entregada)** |
| B2 | Los 3 stacks corriendo el día de la defensa | ⛔ **FALLA** | Stack OTel no existe |
| B3 | Existe `docs/adr/0012-stack-de-observabilidad-final.md` | ⛔ **FALLA** | **Archivo no existe en el repositorio** |
| B4 | ADR `0012` tiene ≥ 1500 palabras (contar antes de corregir) | ⛔ **FALLA** | No aplica (archivo inexistente) |

**Palabras contadas en ADR `0012`:** N/A — archivo no existe

**¿Pasa verificación bloqueante?** ⛔ **NO** — nota = **0**, fin de corrección

---

## CORRECCIÓN DETENIDA POR BLOQUEANTES B1, B3

**B1:** La Parte 3 (OTel) no fue entregada — nota 0/10. El bloqueante B1 de Parte 4 requiere que las tres partes previas estén aprobadas.

**B3:** El archivo `docs/adr/0012-stack-de-observabilidad-final.md` no existe.

Adicionalmente, el directorio `docs/observability-final/` no existe:
- `docs/observability-final/measurements.md` — ausente
- `docs/observability-final/decision-matrix.md` — ausente
- `docs/observability-final/vendor-lockin-essay.md` — ausente

El ADR `0010-instrumentacion-vendor-neutral.md` tampoco existe (gap de Parte 3).

---

## NOTA FINAL TP2 PARTE 4: **0 / 10**

---

## Devolución General

**Lo que hay que entregar para esta parte:**

```
1. docs/observability-final/measurements.md
   — 5 métricas (M1-M5) con comando exacto + timestamp + estado del cluster
   — M1: kubectl top pods (3 muestras separadas, una por stack)
   — M2: du -sh en PVC tras 24h de logs del scraper
   — M3: time curl 10 runs (misma query en LogQL, KQL y OTel OTLP)
   — M4: deploy time clean cluster → primer log visible en UI
   — M5: docker image inspect Promtail, Fluent Bit, OTel Collector

2. docs/observability-final/decision-matrix.md
   — Tabla 5×5: contextos × stacks (Loki / EFK / OTel / Datadog / Splunk)
   — Contextos: Startup OSS-only / Mid enterprise / Regulated / Edge-IoT / Cloud-native
   — Cada celda: ✅/⚠️/❌ + razón ≤25 palabras + caveat ≤20 palabras

3. docs/adr/0012-stack-de-observabilidad-final.md (≥1500 palabras — BLOQUEANTE)
   — 8 secciones: Contexto / Alternativas / Decisión / Trade-offs / Evidencia /
     Plan evolución / Relación ADRs previos / Referencias
   — §5 debe citar mediciones de measurements.md ≥3 veces con números
   — §7 debe mencionar 0007, 0009 y 0010

4. docs/observability-final/vendor-lockin-essay.md (~500 palabras, máx 700)
   — Caso Elastic License v2 (2021) + fork OpenSearch (ya en ADR 0009 ✓)
   — ≥2 empresas reales con links verificables
   — Cierre honesto: OTel redistribuye el lock-in, no lo elimina

5. docs/adr/0010-instrumentacion-vendor-neutral.md (también falta de Parte 3)
   — Mencionar: lock-in Grafana Labs + Elastic, costo 2 agentes vs 1,
     adopción OTLP por Datadog/New Relic/Dynatrace/Splunk, ROI re-instrumentar
```

**Contexto para el grupo:**
```
La Parte 4 depende de la Parte 3: sin OTel corriendo no se pueden tomar las
mediciones M1-M3 (que comparan los 3 stacks) ni escribir el ADR 0012 con
datos propios del cluster.

El orden natural es:
  1. Completar Parte 3 (otel/ + ADR 0010)
  2. Con los 3 stacks corriendo, tomar las mediciones M1-M5
  3. Con los datos reales, escribir ADR 0012 (≥1500 palabras), decision-matrix, vendor-lockin-essay

El ADR 0009 ya tiene la base comparativa (Loki vs EFK con datos reales,
ELv2 + OpenSearch). Esa misma calidad de análisis aplicada al ADR 0012
— que agrega OTel como tercer stack — es lo que se necesita para la Parte 4.

Nota proyectada si se completa Parte 3 y luego Parte 4: dado el nivel de las
Partes 1 y 2, es esperable obtener ≥ 8.5/10 en ambas si se entregan completas.
```
