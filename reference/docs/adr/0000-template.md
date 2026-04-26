# 000X — <Título corto, en imperativo>

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Deprecated | Superseded by 000Y
- **Deciders:** <integrantes que tomaron la decisión>

## Contexto

Describir el problema o trade-off que se enfrenta. ¿Qué fuerzas están en juego (técnicas, organizacionales, de costos, de plazos)? ¿Cuáles son las alternativas que se consideraron y por qué?

Mantener entre 2 y 4 párrafos cortos. La regla de oro: si dentro de 6 meses alguien lee este ADR, debería entender por qué la decisión tenía sentido en ese momento, sin tener que reconstruir el contexto desde cero.

## Decisión

Una oración clara, en voz activa, en presente o pretérito perfecto:

> Decidimos usar **<tecnología/patrón/enfoque>** porque **<razón principal>**.

Si la decisión tiene sub-decisiones (ej: versión específica, configuración default), enumerarlas como bullets debajo. No mezclar la decisión con la justificación: la justificación va en Contexto, las implicancias en Consecuencias.

## Consecuencias

- **Lo que se vuelve más fácil:** capacidades nuevas, simplificaciones, alineación con estándares de la industria.
- **Lo que se vuelve más difícil o se sacrifica:** complejidad agregada, dependencias nuevas, deuda técnica aceptada conscientemente.
- **Riesgos conocidos y mitigaciones:** qué puede salir mal, cómo lo detectamos, qué hacemos si pasa.

Esta sección debe ser honesta: si la decisión tiene un costo real, dejarlo escrito. Un ADR que solo lista beneficios no es un ADR, es marketing.

## Referencias

- Documentación oficial relevante.
- Papers, charlas o blog posts que informaron la decisión.
- ADRs relacionados (que esta decisión deroga, complementa o supersede).
- Issues o discusiones internas (links a Discord, GitHub, etc.).
