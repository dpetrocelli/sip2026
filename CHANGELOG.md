# Changelog

Todos los cambios relevantes de la consigna SIP 2026 se documentan en este archivo.

El formato sigue [Keep a Changelog 1.1](https://keepachangelog.com/en/1.1.0/) y las fechas
usan ISO 8601 (`YYYY-MM-DD`). Las entradas se listan en orden cronológico inverso (lo más
reciente arriba).

## [Unreleased]

_Sin cambios en curso._

## [2026-04-27]

### Added — TP 2 nuevo: Observabilidad en 4 partes
- **TP 2 · Parte 1** (Loki + Promtail/Alloy + Grafana, entrega 05/05/2026) (#23 + #24).
- **TP 2 · Parte 2** (EFK = Elasticsearch + Fluent Bit + Kibana, entrega 05/05/2026 bundle con P1) (#24).
- **TP 2 · Parte 3** (OpenTelemetry Collector + SDK + multi-backend, entrega 09/05/2026) (#24).
- **TP 2 · Parte 4** (Cierre + ADR magisterial, entrega 09/05/2026 bundle con P3) (#24).
- Reference de TP 2 en `reference/tp3-observability/` con Helm values pinneados (Loki/Alloy/Grafana 2026 LTS), dashboards Grafana JSON, queries LogQL, snippet de JSON logging.
- `reference/hit8/` con skeleton PostgreSQL para TP 1·P2 Hit #8: k8s manifests (Secret, ConfigMap, StatefulSet, Service), schema migration SQL, módulo Python con psycopg3 (#23).
- ADRs nuevos en `reference/docs/adr/`: 0007 (postgres-statefulset), 0008 (loki-vs-elk).
- Material de apoyo de TP 2 (TP 1·P2): esqueletos de logging Python, sample tests con mocks, pre-commit Node/Java equivalentes (#23).
- Validador `scripts/validate-site.sh` (anchors, links, assets, branding, placeholders, CSS sanity) (#23).
- Workflow GitHub Actions (`.github/workflows/build-pages.yml`) para auto-build de HTMLs (#21).
- Header UNLu del template clickeable como link al menú principal (#22).
- Referencias bibliográficas al hueso por Hit en TP 1 y TP 1·P2 (papers, docs oficiales, artículos directos) sin libros generales — ya en TP 0 (#20).

### Changed — calendario y estructura
- **Calendario consolidado**: TP 1·P2 = 02/05, TP 2·P1+P2 bundle = 05/05, TP 2·P3+P4 bundle = 09/05 (#25, #27, #28).
- TP 2 (antes 1 documento) partido en 4 partes con prev/next nav threading e index card por parte (#24).
- Bibliografía de TP 1·P2 reordenada: Infra base primero, después por Hit (#22).
- Hit #9 de TP 1·P2 deja de ser bonus → es obligatorio con 3 capacidades fijas (paginación + estadísticas + histórico PostgreSQL en k3s) (#19).
- ADR numbering deduplicado en TP 2: 0007 (Loki) → 0008 (Alloy bonus) → 0009 (EFK) → 0010 (OTel) → 0011 (traces bonus) → 0012 (master magisterial) (#26).
- Hits TP 1·P2 renumerados: secuencia 4-5-6-7-8 sin saltos (Infra base = bloqueante sin número) (#16).
- Pin de versiones Docker obligatorio en TP 1·P2: `python:3.13-slim-trixie`, `node:24-trixie-slim`, `eclipse-temurin:25-jre-noble`, `maven:3.9-eclipse-temurin-25-noble` (#13).
- Dockerfile + docker-compose.yml ahora son **obligatorios desde Parte 1** (antes "deseable") (#11).
- TP 1·P2 rúbrica: Hit #4 25%, Hit #5 15%, Hit #6 15%, Hit #7 20%, Hit #8 15%, ADRs 10% = 100%, todos múltiplos de 5 (#15).
- Reference Dockerfile pasa a Google Chrome stable + `useradd --create-home` para resolver bug crashpad de chromium-trixie y ENOENT en `~/.local/...` (#21).
- Resource limits del Job en `reference/hit8/k8s/job.yaml` subidos a 768Mi/1.5Gi (Chrome OOMKilled con 512Mi) (#21).

### Fixed
- Footer + breadcrumb + prev/next nav del template ahora cubre la cadena completa Inicio → TP 0 → TP 1·P1 → TP 1·P2 → TP 2·P1 → P2 → P3 → P4 (#21, #24).
- `reference/README.md` actualizado con los 8 links a las consignas vigentes.
- Validador `validate-site.sh` reporta 8 HTMLs, 0 errors, 0 warnings.

### Changed
- TP2 Hit #8: ahora son **3 capacidades obligatorias** en lugar de un menú de 6 a
  elegir 1 (#19).
- Reordenamiento del Hit #8 de TP2 para que quede junto al Hit #7 (#18).
- Renumeración de los hits de TP2: secuencia limpia 4-5-6-7-8 sin saltos (#16).

### Fixed
- TP2: la sección "Infra base" deja de duplicarse y queda consolidada en requisitos
  (#17).

## [2026-04-26]

### Changed
- Rúbrica TP2: separa requisitos bloqueantes del puntaje numérico para clarificar qué
  se evalúa (#15).
- Rúbrica TP2: puntajes redondeados a múltiplos de 5 y agrupados por dimensión (#14).
- Pin de imágenes Docker por SHA + Hit #9 obligatorio + migración SQLite -> PostgreSQL
  (#13).
- Plantilla HTML: los enlaces externos ahora abren en una pestaña nueva (#12).
- ADRs: se ofrece un menú de 6 propuestos; eligen 2 + escriben 2 propios (mínimo 4
  total) (#10).
- TP1: `Dockerfile` y `docker-compose` pasan a ser obligatorios desde la Parte 1; nav
  reordenado en stack vertical (#7).

### Removed
- TP2: se quita el callout "Implementación de referencia disponible" para no condicionar
  la entrega (#11).
- Reverted #8 ("Reference como páginas HTML del sitio + deep links contextuales") por
  incompatibilidad con el flujo de build (#9).

## [2026-04-25]

### Added
- TP0: agregado el **Camino C** (push a registry público) y panorama de registries
  vigentes en 2026 (#4).
- Cierre production-ready de TP1 con la implementación de referencia validada E2E en
  k3d (#1).

### Changed
- TP0 alineado a `ghcr.io` como registry recomendado; nav uniforme con "Volver al menú
  principal"; cleanup general de TP1 (#5).
- `Dockerfile` + `docker-compose`: deseables en Parte 1, obligatorios en Parte 2 (#6,
  reemplazado luego por #7).
- Reemplazo del placeholder de Discord por el canal real de la materia (#3).
- Unificación de criterios "calidad + README + Dockerfile" bajo una sola dimensión
  "Infra base" con peso 30% (#2).

---

Para la lista completa de versiones publicadas (cuando existan), ver la
[página de Releases](https://github.com/dpetrocelli/sip2026/releases).
