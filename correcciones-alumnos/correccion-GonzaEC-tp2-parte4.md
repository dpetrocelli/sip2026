# Corrección TP2 — Parte 4: Cierre — Comparativa, decisiones arquitectónicas y ADR magisterial

**Grupo:** ONE
**Integrantes:**
- Anito, Cristian
- Soto, Roberto
- Claros, Federico
- Romero, Nicolas
- Buzzo Marcelo, Rocco
- Echeverria Crenna, Gonzalo
**Repo GitHub:** https://github.com/GonzaEC/TP2-SIP
**Fecha de defensa oral:** _______________________________________________
**Fecha de corrección:** 2026-05-09
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Partes 1, 2 y 3 entregadas y aprobadas (≥ 60/100 cada una) | ✅ OK | P1: 9.7, P2: 9.7, P3: 7.4 |
| B2 | Los 3 stacks corriendo el día de la defensa (`kubectl get pods -A` muestra `observability`, `elastic`, `otel` Running) | ☐ OK / ☐ FALLA | Verificar en defensa |
| B3 | Existe `docs/adr/0012-stack-de-observabilidad-final.md` | ✅ OK | 17,343 bytes ✓ |
| B4 | ADR `0012` tiene ≥ 1500 palabras (contar antes de corregir) | ✅ OK | ~3,850 palabras ✓ |

**Palabras contadas en ADR `0012`:** ~3,850

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

**Penalización automática:** stack(s) caídos al momento de la defensa → **-15 pts**
Stacks caídos (si aplica): _______________________________________________ (completar en defensa)

---

## HIT #1 — Mediciones empíricas en el cluster propio (15 puntos)

### 1.1 Estructura y trazabilidad (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `docs/observability-final/measurements.md` con tabla en formato obligatorio (7 filas × 3 stacks) | 2 | 2 | 4,882 bytes; todas las métricas presentes ✓ |
| Cada celda tiene: comando exacto + timestamp de cuando se tomó + estado del cluster en ese momento | 2 | 1 | M1/M4/M5 tienen datos concretos con timestamps. M3 tiene estructura documentada pero tabla incompleta (p50/p95 sin los 10 runs). |
| Si alguna medición era imposible de tomar, está declarada explícitamente | 1 | 1 | ✓ |

**Subtotal 1.1:** 4 / 5

### 1.2 Las 5 métricas obligatorias presentes (8 pts)

| Métrica | Presente | Tiene comando | Tiene timestamp | Pts |
|---------|----------|--------------|-----------------|-----|
| M1 — RAM/CPU por stack (`kubectl top pods`, 3 muestras espaciadas) | ✅ | ✅ | ✅ | 2 |
| M2 — Disk usage PVC tras 24h de logs del scraper (`kubectl exec ... du -sh`) | ✅ | ✅ | ✅ | 2 |
| M3 — Query latency p50/p95 (misma pregunta en LogQL, KQL y OTel, 10 runs `time curl`) | ✅ | ✅ | ⚠️ | 1 |
| M4 — Tiempo deploy desde clean cluster → primer log visible en UI | ✅ | ✅ | ✅ | 1 |
| M5 — Tamaño imagen del agente (`docker image inspect`) | ✅ | ✅ | ✅ | 1 |

> M1: Loki 35±10 mCPU/369±22 MiB · EFK 84±27 mCPU/2,171±31 MiB · OTel 9±2 mCPU/90±4 MiB
> M4: Loki 238s · EFK 549s · OTel 493s
> M5: Promtail 76.4 MiB · Fluent Bit 39.4 MiB · OTel Collector 73.3 MiB
> M3: estructura documentada pero sin los 10 runs de `time curl` con resultados p50/p95

**Subtotal 1.2:** 7 / 8

### 1.3 Screenshots de evidencia (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existen screenshots en `docs/observability-final/screenshots/` (kubectl-top, pvc-disk-usage, query-latency-comparison) | 2 | 1 | Screenshots de los hits están en `otel/screenshots/` y `efk/screenshots/`. No se encontró un directorio `docs/observability-final/screenshots/` dedicado. |

**Subtotal 1.3:** 1 / 2

### Observaciones Hit #1
```
Mediciones sólidas con datos concretos y comparativos entre los 3 stacks.
M3 es el único gap: la metodología está documentada pero faltan los 10 runs de
`time curl` con resultados numéricos (p50 y p95 por stack). Este es el tipo de
dato que la cátedra puede pedir reproducir en la defensa.
```

**TOTAL HIT #1:** 12 / 15

---

## HIT #2 — Decision matrix por contexto (5 × 5) (15 puntos)

### 2.1 Completitud (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Las 5 filas de contexto presentes: Startup OSS-only / Mid enterprise / Regulated / Edge-IoT / Cloud-native multi-region | 2 | 2 | ✓ |
| Las 5 columnas de stack presentes: Loki / EFK / OTel Collector / Datadog / Splunk | 1 | 1 | ✓ |
| Las 25 celdas completas — ninguna vacía ni con "N/A" sin justificar | 2 | 2 | ✓ |

**Subtotal 2.1:** 5 / 5

### 2.2 Calidad de las celdas (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Todas las celdas tienen veredicto explícito (✅/⚠️/❌) | 2 | 2 | ✓ |
| Las razones son específicas — no genéricas del tipo "es bueno" | 3 | 3 | Ejemplo: "Elasticsearch ofrece full-text search superior y ML nativo (Elastic SIEM); justificable si ya hay expertise interno" ✓ |
| Los caveats son reales — describen condiciones que cambiarían el veredicto | 3 | 3 | Ejemplo: "equipo de plataforma de 2–4 personas sufrirá con cluster management" ✓ |

**Subtotal 2.2:** 8 / 8

### 2.3 Consistencia con mediciones del Hit #1 (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los veredictos son coherentes con los números medidos en Hit #1 (no contradicen la tabla) | 2 | 2 | EFK marcado ⚠️ en Startup por footprint medido de 2,171 MiB; consistente ✓ |

**Subtotal 2.3:** 2 / 2

**TOTAL HIT #2:** 15 / 15

---

## HIT #3 — ADR magisterial `0012-stack-de-observabilidad-final.md` (50 puntos)

### 3.1 Estructura — las 8 secciones de la plantilla (8 pts)

| Sección | Presente | Extensión adecuada | Pts |
|---------|----------|--------------------|-----|
| §1 Contexto (300-400 palabras) — escenario con números concretos | ✅ | ✅ | 1 |
| §2 Alternativas consideradas (400-500 palabras) — las 5 stacks | ✅ | ✅ | 1 |
| §3 Decisión (150-250 palabras) — veredicto en negrita al inicio | ✅ | ✅ | 1 |
| §4 Trade-offs aceptados explícitos (200-300 palabras) — 3-5 renuncias | ✅ | ✅ | 1 |
| §5 Evidencia empírica (100-200 palabras) — cita Hit #1 ≥ 3 veces con números | ✅ | ✅ | 1 |
| §6 Plan de evolución (200-300 palabras) — 3 horizontes: 6/12/24 meses | ✅ | ✅ | 1 |
| §7 Relación con ADRs previos (100-150 palabras) — 0007, 0009, 0010 | ✅ | ⚠️ | 0 |
| §8 Referencias — documentos y links citados | ✅ | ✅ | 1 |

> §7: el ADR menciona 0007 (parcial) y 0009 (supersedido), pero no menciona 0010 explícitamente.

**Subtotal 3.1:** 7 / 8

### 3.2 §1 Contexto — calidad del escenario (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El escenario es concreto y tiene números: tamaño de equipo, presupuesto, volumen de logs, restricciones regulatorias | 3 | 3 | 4-persona full-stack, USD 280/month AWS EKS, 300 MB/day logs actuales → 3 GB/day en 12 meses (150 stores vs 15) ✓ |
| No es una mega-empresa genérica — es representativo de algo real y alcanzable para el equipo | 2 | 2 | Escenario de startup de scraping de precios muy concreto ✓ |

**Subtotal 3.2:** 5 / 5

### 3.3 §2 Alternativas — profundidad del análisis (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los 3 stacks operados (Loki/EFK/OTel) tienen pro + contra en el contexto del §1 — no genérico | 3 | 3 | Cada uno con footprint medido, costo estimado, y contexto del escenario ✓ |
| Datadog y Splunk están analizados aunque no los hayan desplegado (conocimiento de mercado) | 2 | 2 | Datadog USD 114/month ingestion; Splunk similar costo ✓ |
| Cada alternativa cita al menos un número de la tabla del Hit #1 | 1 | 1 | ✓ |

**Subtotal 3.3:** 6 / 6

### 3.4 §3 Decisión — claridad y solidez del veredicto (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Veredicto concreto en la primera línea (no "depende" sin resolución) | 3 | 3 | "Adopt OTel Collector + Loki + Grafana with 6-month plan to add Tempo" ✓ |
| Justifica por qué el stack elegido gana en el contexto del §1 vs las alternativas del §2 | 3 | 3 | RAM (6.6× menor que EFK), costo (USD 30+/month ahorrado), velocidad MTTR 57% mejor ✓ |
| Declara umbrales que cambiarían la decisión | 2 | 2 | 6m: >1GB/day + traces → Tempo; 12m: >3GB/day + 6 personas → Loki distribuido; 24m: 10+ personas + USD 800+/month → reevaluar Datadog/Splunk ✓ |

**Subtotal 3.4:** 8 / 8

### 3.5 §4 Trade-offs — honestidad de las renuncias (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Al menos 3 trade-offs explícitos con formato "renunciamos a X porque Y, mitigación: Z" | 4 | 4 | 4 trade-offs: full-text search, HA single-binary, complejidad OTel, correlación manual logs-métricas-traces ✓ |
| Los trade-offs son reales — no los minimizan ni los disfrazan de ventajas | 2 | 2 | Reconocen limitaciones concretas con condiciones de activación ✓ |

**Subtotal 3.5:** 6 / 6

### 3.6 §5 Evidencia — citas del Hit #1 (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| La tabla del Hit #1 está referenciada al menos 3 veces en el cuerpo del ADR con números concretos | 3 | 3 | "324 MiB RAM", "2142 MiB RAM", "84 MiB RAM", "USD 114/month", "6.6× Loki's footprint", "12-18% del presupuesto total" ✓ |
| Los números citados son consistentes con `measurements.md` (no redondeados de forma engañosa) | 1 | 1 | Coherentes ✓ |

**Subtotal 3.6:** 4 / 4

### 3.7 §6 Plan de evolución — especificidad (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los 3 horizontes (6/12/24 meses) tienen: trigger específico + acción concreta + riesgo si no se hace | 4 | 4 | ✓ (ver umbrales en §3.4) |
| No dicen "vamos a evaluar de nuevo" sin describir qué evento o métrica dispara la evaluación | 1 | 1 | Triggers: volumen de logs, tamaño de equipo, presupuesto disponible — todos concretos ✓ |

**Subtotal 3.7:** 5 / 5

### 3.8 §7 Relación con ADRs previos (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Menciona 0007 (Loki), 0009 (EFK), 0010 (OTel) — qué sigue válido y qué se actualiza | 2 | 1 | 0007: "backend inherited; agent replaced" ✓ · 0009: "explicitly closed" ✓ · **0010: no mencionado** |
| Declara si este ADR supercede total o parcialmente alguno de los anteriores | 1 | 1 | Supersede parcialmente 0007, totalmente 0009 ✓ |

**Subtotal 3.8:** 2 / 3

### 3.9 Calidad general de la prosa (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Lenguaje técnico y sobrio — sin hype, sin adjetivos vacíos, sin contradicciones internas | 3 | 3 | Prosa técnica, cuantitativa, sin frases de marketing ✓ |
| Coherencia interna: §1 → §2 → §3 → §4 forman un argumento que se sostiene solo | 2 | 2 | Escenario de §1 sostiene la decisión de §3; trade-offs de §4 son consecuencias directas ✓ |

**Subtotal 3.9:** 5 / 5

### Observaciones Hit #3
```
ADR de muy alta calidad. ~3,850 palabras, datos cuantitativos propios, trade-offs honestos,
plan de evolución con triggers concretos. Es uno de los mejores ADRs del curso.

El único gap es §7: no menciona ADR 0010 (OTel vendor-neutral), que debería aparecer
como "sigue válido — este ADR lo ejecuta". Con ese agregado, sería un 50/50.
```

**TOTAL HIT #3:** 48 / 50

---

## HIT #4 — Reflexión sobre vendor lock-in (15 puntos)

**Palabras contadas:** ~1,100 (excede el máximo de 700 palabras en un 57%)

### 4.1 Estructura del essay (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Cubre las 5 partes: apertura / qué cambia con OTel / CNCF graduated / casos reales / cierre honesto | 3 | 3 | Las 5 secciones están claramente delimitadas ✓ |

**Subtotal 4.1:** 3 / 3

### 4.2 Contenido técnico (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Explica correctamente que el lock-in histórico era el SDK del vendor, no el backend | 2 | 2 | "SDK (ahora neutral) / Protocolo OTLP (estándar abierto) / Almacenamiento (sigue siendo propietario)" ✓ |
| Explica cómo OTel desacopla SDK (estándar) de backend (reemplazable via YAML del Collector) | 3 | 3 | ✓ |
| Menciona que CNCF graduated (2024) implica gobernanza multi-vendor y no-fork | 2 | 2 | Sección dedicada a CNCF graduated ✓ |
| Cita el caso de Elastic License v2 (2021) y el fork OpenSearch como ejemplo de lock-in de licencia | 1 | 0 | **Ausente.** El essay no menciona ELv2 ni OpenSearch. Irónico dado que todo el TP usa Elasticsearch. |

**Subtotal 4.2:** 7 / 8

### 4.3 Casos reales con cita verificable (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Al menos 2 empresas reales citadas con link verificable | 3 | 3 | Shopify (Elijah McPherson, Feb 2025) ✓ · Cruise/GM (KubeCon NA 2023) ✓ · Grafana Labs ✓ |

**Subtotal 4.3:** 3 / 3

### 4.4 Cierre honesto (1 pt)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El cierre reconoce que OTel redistribuye el lock-in (no lo elimina) | 1 | 1 | "OpenTelemetry redistribuye el lock-in en lugar de eliminarlo" — cita directa ✓ |

**Subtotal 4.4:** 1 / 1

### Observaciones Hit #4
```
Essay técnicamente correcto y con cierre honesto excelente. El único gap: no mencionar
Elastic License v2 (2021) y el fork OpenSearch siendo que todo el TP construyó un stack
con Elasticsearch. Sería el ejemplo más cercano y poderoso para ilustrar lock-in de licencia.

El exceso de palabras (1,100 vs 700 máx) no resta puntos pero indica que podría
sintetizarse mejor — la cátedra valora prosa técnica concisa.
```

**TOTAL HIT #4:** 14 / 15

---

## DEFENSA ORAL (5 puntos)

> A completar durante la sesión de defensa.

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El equipo presenta el ADR magisterial con claridad — puede resumir la decisión y los trade-offs en 2 minutos | 2 | | |
| Las preguntas del jurado sobre los números del Hit #1 son respondidas con referencia a los datos medidos | 2 | | |
| El equipo puede defender su veredicto ante contraejemplos planteados por el jurado | 1 | | |

### Preguntas sugeridas para la defensa
```
1. "¿Por qué eligieron Loki sobre EFK si EFK tiene mejor full-text search?"
   (esperado: citar M1 RAM, M4 deploy time, costo USD 30/month)

2. "¿Qué pasa si el día de mañana Grafana Labs cambia la licencia de Loki como hizo
   Elastic con ELv2 en 2021?" (esperado: mencionar que OTel desacopla el agente del backend)

3. "En Hit #5 de Parte 3, el trace_id estaba vacío. ¿Cómo planean instrumentar el scraper?"

4. "M3 no tiene los 10 runs de latency. ¿Pueden reproducir la medición ahora?"
```

**TOTAL DEFENSA ORAL:** ___ / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 4

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — Mediciones empíricas (tabla + comandos + timestamps) | 15% | 12 | 15 |
| Hit #2 — Decision matrix 5×5 (veredicto + razón + caveat) | 15% | 15 | 15 |
| Hit #3 — ADR magisterial ≥ 1500 palabras, 8 secciones ⭐ | 50% | 48 | 50 |
| Hit #4 — Reflexión vendor lock-in ~500 palabras, ≥ 2 casos reales | 15% | 14 | 15 |
| Defensa oral | 5% | ___ | 5 |
| **TOTAL** | **100%** | **89 + defensa** | **100** |
| Penalización: stack(s) caídos en defensa | | | -15 |

### Nota Final TP2 Parte 4: (89 + defensa) / 10

> Sin defensa: 8.9/10. Con defensa 5/5: 9.4/10. Con defensa 4/5: 9.3/10.

---

## Devolución General

**Fortalezas:**
```
ADR 0012 excepcional: ~3,850 palabras, datos cuantitativos propios, 4 trade-offs explícitos
con mitigaciones, plan de evolución con triggers concretos. Uno de los mejores del curso.
Decision matrix 5×5 completa con celdas bien justificadas y consistente con mediciones.
Essay de vendor lock-in con cierre honesto ("redistribuye, no elimina") — pocas entregas
llegan a esa conclusión.
```

**Puntos a mejorar:**
```
M3 en measurements.md: completar los 10 runs de time curl por backend con p50/p95.
§7 del ADR 0012: mencionar ADR 0010 (OTel vendor-neutral) como "sigue válido y este ADR lo ejecuta".
Essay: agregar caso ELv2 (2021) + fork OpenSearch — es el ejemplo más cercano al TP.
```

**Comentarios para el grupo:**
```
La Parte 4 es la más sólida de todo el TP2. La historia técnica está bien contada
y los números son propios y concretos. El único gap en el ADR (§7 sin 0010) y en
el essay (sin ELv2/OpenSearch) son correcciones de 10 minutos.

Para la defensa: prepárense para preguntas sobre Hit #5 de Parte 3 (trace_id vacío)
ya que el jurado va a notar la inconsistencia entre el OTel Collector bien configurado
y la falta de SDK en el scraper. El ADR 0012 prometió OTel como stack final — van a
preguntar si el scraper realmente emite OTLP.
```
