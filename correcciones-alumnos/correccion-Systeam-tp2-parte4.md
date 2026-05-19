# Corrección TP2 — Parte 4: Cierre — Comparativa, decisiones arquitectónicas y ADR magisterial

**Grupo:** Systeam
**Integrantes:**
- Hoffmann, Axel
- Babino, Abril
- Avila, Tobias
- Collazo, Naiara
- Nomico, Mateo
- Casal, Ulises
**Repo GitHub:** https://github.com/UlisesCasal/SIP-Selenium-Systeam
**Fecha de defensa oral:** _______________________________________________
**Fecha de corrección:** 2026-05-09 → **re-corrección: 2026-05-11** (entrega 2026-05-14)
**Corrector:** M. Rapaport

> Nota original: **0/10** (bloqueante B3 — ADR 0012 inexistente).
> Re-corrección tras push del 14 de mayo con todos los entregables.

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Partes 1, 2 y 3 entregadas y aprobadas (≥ 60/100 cada una) | ✅ OK | P1: 9.7, P2: 9.6, P3: 9.5 (re-corregida) |
| B2 | Los 3 stacks corriendo el día de la defensa | ☐ OK / ☐ FALLA | Verificar en defensa |
| B3 | Existe `docs/adr/0012-stack-de-observabilidad-final.md` | ✅ OK | Presente — entregado 2026-05-14 |
| B4 | ADR `0012` tiene ≥ 1500 palabras (contar antes de corregir) | ✅ OK | **2,847 palabras** ✓ |

**Palabras contadas en ADR `0012`:** 2,847 palabras

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

**Penalización automática:** stack(s) caídos en defensa → -15 pts. Stacks caídos: _______________

---

## HIT #1 — Mediciones empíricas en el cluster propio (15 puntos)

### 1.1 Estructura y trazabilidad (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `docs/observability-final/measurements.md` con tabla en formato obligatorio | 2 | 2 | ~1847 palabras, tabla 7 filas × 3 stacks ✓ |
| Cada celda tiene: comando exacto + timestamp + estado del cluster | 2 | 2 | Todos con timestamps ART y estado de cluster documentado ✓ |
| Mediciones imposibles declaradas explícitamente | 1 | 1 | Todas las métricas tomadas; imposibilidades indicadas donde aplica ✓ |

**Subtotal 1.1:** 5 / 5

### 1.2 Las 5 métricas obligatorias (8 pts)

| Métrica | Presente | Tiene comando | Tiene timestamp | Pts |
|---------|----------|--------------|-----------------|-----|
| M1 — RAM/CPU por stack (`kubectl top pods`, 3 muestras) | ✅ | ✅ | ✅ 2026-05-10T14:48 ART | 2 |
| M2 — Disk usage PVC tras 24h (`kubectl exec ... du -sh`) | ✅ | ✅ | ✅ 2026-05-10T16:00 ART | 2 |
| M3 — Query latency p50/p95 (LogQL, KQL, OTel, 10 runs `time curl`) | ✅ | ✅ | ✅ 2026-05-10T16:30 ART | 2 |
| M4 — Deploy time clean cluster → primer log visible en UI | ✅ | ✅ | ✅ 2026-05-11T01:08→01:12 ART | 1 |
| M5 — Tamaño imagen del agente (`docker image inspect`) | ✅ | ✅ | ✅ 2026-05-10 | 1 |

**Subtotal 1.2:** 8 / 8

### 1.3 Screenshots de evidencia (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existen screenshots en `docs/observability-final/screenshots/` (kubectl-top, pvc-disk-usage, query-latency-comparison) | 2 | 1 | Carpeta screenshots/ no confirmada en el árbol del repo. Comandos y outputs documentados con precisión en measurements.md pero sin capturas visuales. |

**Subtotal 1.3:** 1 / 2

### Observaciones Hit #1
```
Measurements.md es el más completo de los cuatro grupos. Estado del cluster
documentado para cada medición, 3 muestras separadas para M1, cluster state
table al inicio. Los timestamps y comandos son reproducibles.

Datos clave:
  M1 RAM: Loki 239 MiB · EFK 2,099 MiB · OTel 115 MiB
  M2 Disco PVC: Loki 1.8 MiB · ES 69 MiB · OTel 0 (no persiste)
  M3 Latencia p95: Loki 50 ms · ES 85 ms · OTel 42 ms
  M4 Deploy time: Loki 244 s · EFK 121 s · OTel 31 s
  M5 Imagen: Promtail ~100 MB · Fluent Bit ~73 MB · OTel Collector ~128 MB
```

**TOTAL HIT #1:** 14 / 15

---

## HIT #2 — Decision matrix por contexto (5 × 5) (15 puntos)

### 2.1 Completitud (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Las 5 filas de contexto presentes (Startup OSS-only / Mid enterprise / Regulated / Edge-IoT / Cloud-native) | 2 | 2 | C1-C5 presentes ✓ |
| Las 5 columnas de stack presentes (Loki / EFK / OTel / Datadog / Splunk) | 1 | 1 | S1-S5 presentes ✓ |
| Las 25 celdas completas — ninguna vacía ni con "N/A" sin justificar | 2 | 2 | 25/25 celdas completas ✓ |

**Subtotal 2.1:** 5 / 5

### 2.2 Calidad de las celdas (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Todas las celdas tienen veredicto explícito (✅/⚠️/❌) | 2 | 2 | ✓ |
| Las razones son específicas — no genéricas | 3 | 3 | Citan cifras de measurements.md (239 MiB, $0, 9× diferencia, etc.) ✓ |
| Los caveats son reales — describen condiciones que cambiarían el veredicto | 3 | 3 | "Si necesitan full-text search en 12 meses, migrar a OTel antes" ✓ |

**Subtotal 2.2:** 8 / 8

### 2.3 Consistencia con mediciones del Hit #1 (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los veredictos son coherentes con los números medidos en Hit #1 | 2 | 2 | C1/S2 ❌ cita "2,099 MiB" de measurements.md para justificar el veto ✓ |

**Subtotal 2.3:** 2 / 2

**TOTAL HIT #2:** 15 / 15

---

## HIT #3 — ADR magisterial `0012-stack-de-observabilidad-final.md` (50 puntos)

### 3.1 Estructura — las 8 secciones (8 pts)

| Sección | Presente | Extensión adecuada | Pts |
|---------|----------|--------------------|-----|
| §1 Contexto (300-400 palabras) | ✅ | ✅ | 1 |
| §2 Alternativas consideradas (400-500 palabras) | ✅ | ✅ | 1 |
| §3 Decisión (150-250 palabras) | ✅ | ✅ | 1 |
| §4 Trade-offs aceptados (200-300 palabras) — 3-5 renuncias | ✅ | ✅ | 1 |
| §5 Evidencia empírica (100-200 palabras) — ≥3 citas con números | ✅ | ✅ | 1 |
| §6 Plan de evolución (200-300 palabras) — 3 horizontes | ✅ | ✅ | 1 |
| §7 Relación con ADRs previos (100-150 palabras) | ✅ | ✅ | 1 |
| §8 Referencias | ❌ | — | 0 |

**Subtotal 3.1:** 7 / 8

### 3.2 §1 Contexto — calidad del escenario (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El escenario es concreto con números: equipo, presupuesto, volumen de logs, restricciones | 3 | 3 | Equipo 3-5 personas, ~2.000 log lines/ejecución, single-node k3s ✓ |
| No es una mega-empresa genérica — representativo de algo real y alcanzable | 2 | 2 | Startup de e-commerce price monitoring — concreto y creíble ✓ |

**Subtotal 3.2:** 5 / 5

### 3.3 §2 Alternativas — profundidad del análisis (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los 3 stacks operados tienen pro + contra en el contexto del §1 | 3 | 3 | Loki, EFK y OTel con pros/contras concretos para el escenario ✓ |
| Datadog y Splunk analizados aunque no los desplegaron | 2 | 2 | TCO estimado, casos de uso específicos ✓ |
| Cada alternativa cita al menos un número de Hit #1 | 1 | 1 | "EFK consume 2.099 MiB RAM vs 239 MiB de Loki — 9×" ✓ |

**Subtotal 3.3:** 6 / 6

### 3.4 §3 Decisión — claridad y solidez (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Veredicto concreto en la primera línea (no "depende") | 3 | 3 | "Adoptamos OTel Collector + Loki + Grafana + Jaeger all-in-one, con plan de migrar a Tempo en 12 meses." ✓ |
| Justifica por qué el stack elegido gana en el contexto del §1 | 3 | 3 | ✓ |
| Declara umbrales que cambiarían la decisión | 2 | 2 | Triggers cuantificados en §6 ✓ |

**Subtotal 3.4:** 8 / 8

### 3.5 §4 Trade-offs — honestidad de las renuncias (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Al menos 3 trade-offs explícitos con formato "renunciamos a X porque Y, mitigación: Z" | 4 | 4 | 5 trade-offs explícitos ✓ |
| Los trade-offs son reales — no los minimizan ni disfrazan de ventajas | 2 | 2 | "Jaeger pierde traces al reiniciar" reconocido sin eufemismos ✓ |

**Subtotal 3.5:** 6 / 6

### 3.6 §5 Evidencia — citas del Hit #1 (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| La tabla del Hit #1 referenciada ≥3 veces con números concretos en el cuerpo del ADR | 3 | 3 | 6 citas con valores exactos (239 MiB, 2.099 MiB, 50 ms, 85 ms, 31 s, 244 s) ✓ |
| Los números citados son consistentes con `measurements.md` | 1 | 1 | ✓ |

**Subtotal 3.6:** 4 / 4

### 3.7 §6 Plan de evolución — especificidad (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los 3 horizontes tienen: trigger específico + acción concreta + riesgo si no se hace | 4 | 4 | 6m: "2 GB/día o equipo ≥6 → Jaeger→Tempo"; 12m: ">5 GB/día o LogQL lento → ES secundario"; 24m: "Serie A, 15+, >$5k → Datadog/Grafana Cloud" ✓ |
| No dicen "vamos a evaluar de nuevo" sin describir la métrica que dispara | 1 | 1 | Triggers cuantificados ✓ |

**Subtotal 3.7:** 5 / 5

### 3.8 §7 Relación con ADRs previos (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Menciona 0007, 0009, 0010 — qué sigue válido y qué se actualiza | 2 | 2 | "0007: lo reemplazamos · 0009: lo actualizamos · 0010: lo confirmamos" ✓ |
| Declara si este ADR supercede total o parcialmente a anteriores | 1 | 1 | ✓ |

**Subtotal 3.8:** 3 / 3

### 3.9 Calidad general de la prosa (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Lenguaje técnico y sobrio — sin hype, sin contradicciones internas | 3 | 3 | ✓ |
| Coherencia §1→§2→§3→§4 — argumento que se sostiene solo | 2 | 2 | ✓ |

**Subtotal 3.9:** 5 / 5

### Observaciones Hit #3
```
ADR 0012 de alta calidad. 5 trade-offs con mitigaciones reales y honestas. §6 con
triggers cuantitativos precisos. §7 con cadena completa de ADRs 0007/0009/0010.
6 citas numéricas de measurements.md con valores exactos.

Único gap: §8 Referencias ausente. Una sección final con links a los documentos
citados (measurements.md, ADRs previos, docs oficiales de Loki/OTel/Jaeger)
completa el ADR como documento de referencia.
```

**TOTAL HIT #3:** 49 / 50

---

## HIT #4 — Reflexión sobre vendor lock-in (15 puntos)

**Palabras contadas:** 680 (máx 700 ✓)

### 4.1 Estructura del essay (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Cubre las 5 partes: apertura / qué cambia con OTel / CNCF graduated / casos reales / cierre honesto | 3 | 3 | ✓ |

**Subtotal 4.1:** 3 / 3

### 4.2 Contenido técnico (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Explica correctamente que el lock-in histórico era el SDK del vendor, no el backend | 2 | 2 | ✓ |
| Explica cómo OTel desacopla SDK (estándar) de backend (reemplazable via YAML del Collector) | 3 | 3 | ✓ |
| Menciona CNCF graduated (2024) — gobernanza multi-vendor | 2 | 2 | ✓ |
| Cita Elastic License v2 (2021) y fork OpenSearch como ejemplo | 1 | 1 | "En 2021 Elastic cambió su licencia ... AWS forkeó ES a OpenSearch" ✓ |

**Subtotal 4.2:** 8 / 8

### 4.3 Casos reales con cita verificable (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Al menos 2 empresas reales citadas con link verificable | 3 | 3 | Shopify (shopify.engineering), Discord (discord.com/blog), GitHub (KubeCon 2023) — 3 empresas ✓ |

**Subtotal 4.3:** 3 / 3

### 4.4 Cierre honesto (1 pt)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El cierre reconoce que OTel redistribuye el lock-in (no lo elimina) | 1 | 1 | "OTel no elimina el lock-in. Lo redistribuye ... Eso no es nirvana — es progreso medible." ✓ |

**Subtotal 4.4:** 1 / 1

**TOTAL HIT #4:** 15 / 15

---

## DEFENSA ORAL (5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Presenta el ADR — resume decisión y trade-offs en 2 minutos | 2 | — | Pendiente |
| Preguntas sobre números del Hit #1 respondidas con referencia a datos medidos | 2 | — | Pendiente |
| Puede defender el veredicto ante contraejemplos del jurado | 1 | — | Pendiente |

### Preguntas sugeridas para la defensa
```
1. §6 plantea migrar Jaeger→Tempo "si el equipo crece a 6+ developers".
   ¿Hay un plan de contingencia si ese crecimiento ocurre antes de los 6 meses?

2. M3 muestra OTel p95 = 42 ms y ES p95 = 85 ms. §2 dice que EFK tiene
   "full-text search más rápido que Loki". ¿Están midiendo cosas distintas?
   ¿Cómo reconcilian la latencia de query con la afirmación de §2?

3. §4 trade-off: "Riesgo de lock-in en Grafana — mitigación: dashboards como código".
   Pero el ADR 0010 menciona que Grafana Labs puede cambiar licencia (ya pasó con Loki).
   ¿Por qué eligen Grafana como backend visual si reconocen ese riesgo?
```

**TOTAL DEFENSA ORAL:** ___ / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 4

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — Mediciones empíricas | 15% | 14 | 15 |
| Hit #2 — Decision matrix 5×5 | 15% | 15 | 15 |
| Hit #3 — ADR magisterial 2847 palabras, 7/8 secciones ⭐ | 50% | 49 | 50 |
| Hit #4 — Reflexión vendor lock-in 680 palabras, 3 casos reales | 15% | 15 | 15 |
| Defensa oral | 5% | — | 5 |
| **TOTAL (sin defensa)** | **95%** | **93** | **95** |
| Penalización: stack(s) caídos | | 0 | -15 |

### Nota Final TP2 Parte 4: **9.3 / 10** (sin defensa) · hasta **9.8 / 10** con defensa perfecta

---

## Devolución General

**Fortalezas:**
```
Measurements.md más completo del curso — timestamps, estado del cluster,
3 muestras para M1, datos reproducibles con diferencias medidas empíricamente
(9× entre Loki y EFK, OTel deploya en 31s vs 244s de Loki).

ADR 0012: 5 trade-offs honestos con mitigaciones reales, §6 con triggers
cuantitativos (2 GB/día, 15+ personas, $5k presupuesto), §7 con cadena
de ADRs explícita. Decision matrix con 25 celdas citando datos del cluster.

Vendor lock-in essay: cierre sobrio y preciso — "OTel no elimina el lock-in.
Lo redistribuye ... Eso no es nirvana — es progreso medible."
```

**Puntos a mejorar:**
```
ADR 0012 §8 ausente (−1 pt): agregar sección Referencias con links a
documentación oficial (Loki, OTel, Jaeger) y archivos internos citados.

Screenshots de measurements (−1 pt): agregar carpeta docs/observability-final/
screenshots/ con capturas de kubectl top, du -sh y comparativa de latencia.
```

**Comentarios para el grupo:**
```
La entrega de la Parte 4 es la más completa de los cuatro grupos. Los datos
medidos empíricamente (9× diferencia RAM, OTel desplegando en 31s) son
exactamente el tipo de evidencia que hace a un ADR creíble y defendible.

Para la defensa: el punto más interesante es la aparente contradicción entre
el trade-off de lock-in en Grafana (§4) y la elección de Grafana como backend.
Tener lista una respuesta clara para esa pregunta demuestra que entendieron
los límites de su propia decisión.
```
