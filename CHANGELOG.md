# Changelog

Todos los cambios relevantes de la consigna SIP 2026 se documentan en este archivo.

El formato sigue [Keep a Changelog 1.1](https://keepachangelog.com/en/1.1.0/) y las fechas
usan ISO 8601 (`YYYY-MM-DD`). Las entradas se listan en orden cronológico inverso (lo más
reciente arriba).

## [Unreleased]

### Added
- Workflow de GitHub Actions (`.github/workflows/build-pages.yml`) que regenera los
  `practica-*.html` automáticamente cuando se modifica algún `.md`, `template.html`,
  `build.sh` o `assets/style.css` en `main`.
- Este `CHANGELOG.md` para que los/las estudiantes puedan seguir la evolución de la
  consigna de un vistazo.

## [2026-04-27]

### Added
- Referencias directas (papers, documentación oficial y artículos) al final de TP1 y
  TP2, sin intermediarios (#20).

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
