# 0007 — Usar PostgreSQL como StatefulSet en el cluster en lugar de un servicio managed

- **Date:** 2026-04-26
- **Status:** Accepted
- **Deciders:** Cátedra SIP 2026

## Contexto

El Hit #8 extiende el scraper con **histórico de precios**: cada corrida del `CronJob` ya no solo escribe el JSON a un PVC, sino que persiste cada resultado en una base de datos para poder responder queries del estilo "¿cómo evolucionó el precio promedio del producto X en los últimos 30 días?", "¿qué tiendas oficiales aparecen más seguido en el top 10?", "¿en qué horarios del día baja el precio?". Eso requiere persistencia consultable con SQL — un store ad-hoc en archivos JSON no escala para esa clase de query.

Las alternativas razonables son cuatro:

1. **SQLite local en el PVC.** Cero infraestructura nueva, archivo único, ideal para una sola máquina. Pero el `Job` y el `CronJob` corren en pods distintos que se programan en momentos distintos, y SQLite con varios escritores concurrentes a través del mismo archivo en un PVC `ReadWriteOnce` es una receta para corrupción. Además, no hay TCP — herramientas como `psql`, DBeaver o un dashboard de Grafana no pueden conectarse desde fuera del pod.
2. **PostgreSQL managed (RDS / Cloud SQL / AlloyDB / Neon).** Lo correcto para producción: HA, backups automáticos, point-in-time recovery, parches gestionados. Pero (a) requiere cuenta de cloud con billing activo, (b) saca el TP del modelo "todo corre en el laptop del alumno", (c) agrega un punto de fricción enorme para alumnos que no tienen tarjeta para abrir cuenta en AWS.
3. **DynamoDB / otra NoSQL.** Tira por la borda el modelo de datos relacional que las queries del histórico necesitan (joins, agregaciones temporales, ventanas). Forzaría desnormalización innecesaria para un volumen de datos que es muy chico.
4. **PostgreSQL como `StatefulSet` en el mismo cluster k3s/k3d.** Una sola pieza más para deployar, declarativa (`kubectl apply -f`), reproducible (la imagen `postgres:16-trixie` es bit-exact), persistente vía `volumeClaimTemplates` con storage class `local-path`, y accesible por TCP desde el scraper a través de un `Service` ClusterIP. La transición a producción real es directa: cambiar `StatefulSet` por un operator (CloudNativePG / Zalando / Crunchy Data) o por un DSN apuntando a RDS.

El TP está pensado para que cualquier alumno pueda completarlo con un laptop modesto y sin cuentas en cloud — el énfasis está en el **patrón** ("tu app necesita una base de datos persistente, ¿cómo la metés en Kubernetes?") y no en la operabilidad real ("¿cómo le pongo HA y PITR a esto?"). Eso descarta (2) y (3) por costo y por foco. SQLite (1) se descarta porque el modelo Job + CronJob ya implica múltiples procesos que pueden colisionar en el mismo archivo.

## Decisión

Decidimos desplegar **PostgreSQL 16 como StatefulSet de 1 réplica en el mismo cluster k3s/k3d**, con storage persistido en un PVC vía `volumeClaimTemplates`, exposición interna por un `Service` ClusterIP, y schema inicial cargado automáticamente desde un `ConfigMap` montado en `/docker-entrypoint-initdb.d/`.

Sub-decisiones:

- **Versión:** `postgres:16-trixie` (Postgres 16 LTS, soporte hasta noviembre 2028; Debian 13 trixie como base por consistencia con el Dockerfile del scraper).
- **Réplicas:** 1. Sin replicación, sin HA. Para el TP alcanza.
- **Storage:** 5 Gi sobre `local-path` (Rancher local-path-provisioner que k3s/k3d traen built-in). En cloud sería `gp3` (EKS), `premium-rwo` (GKE) o `managed-premium` (AKS).
- **Secret:** `POSTGRES_PASSWORD` en un `Secret` Opaque con valor base64 hardcodeado en el manifest. Documentado explícitamente como anti-patrón de producción y con punteros a external-secrets / sealed-secrets / Vault para el camino real.
- **Cliente:** `psycopg` (psycopg3, no psycopg2) con `psycopg_pool.ConnectionPool`. Es 2026, psycopg3 está estable desde hace años y es el path forward oficial.

## Consecuencias

- **Lo que se vuelve más fácil:**
  - **Reproducibilidad total:** `kubectl apply -f hit8/k8s/` levanta toda la stack (scraper + Postgres + schema) sin pasos manuales fuera del cluster.
  - **Autocontenido:** no requiere cuenta de cloud, ni billing, ni acceso a internet más allá del pull inicial de la imagen oficial.
  - **Mismas primitivas que producción:** `StatefulSet`, `volumeClaimTemplates`, `Secret`, `ConfigMap`, `Service` ClusterIP — el alumno aprende exactamente las piezas que después va a usar en una empresa, no abstracciones que aplican solo al laptop.
  - **Punto pedagógico:** el alumno tiene que entender por qué `Deployment` + PVC compartido NO sirve para una base de datos (rescheduling rompe la afinidad pod ↔ volumen) y por qué `StatefulSet` + `volumeClaimTemplates` sí. Esa distinción es la que hace la diferencia entre "leí el README de Kubernetes" y "entiendo cómo se opera estado en Kubernetes".

- **Lo que se vuelve más difícil o se sacrifica:**
  - **No hay alta disponibilidad.** Si el nodo donde corre `postgres-0` se cae, la base no está disponible hasta que se levante de nuevo. Para el TP es aceptable; para producción requeriría un operator (CloudNativePG, Zalando) o un servicio managed.
  - **No hay backups automáticos.** Si el PVC se corrompe o se borra accidentalmente, se pierde el histórico. Mitigación pedagógica: documentar `pg_dump` como tarea manual en el README; la solución industrial es Velero, pgBackRest, o snapshots del cloud provider.
  - **Competencia de recursos en el nodo.** El scraper corriendo Chrome headless ya pide 1.5 GiB de memoria; Postgres pide otro 1 GiB. En un k3d sobre un laptop con 8 GB de RAM total y otras apps abiertas, el scheduler puede empezar a evictar pods. Mitigado con `requests`/`limits` razonables (256Mi / 1Gi para Postgres), pero el alumno tiene que estar atento al `kubectl top pods`.
  - **`Secret` con password en claro en el repo.** Es una violación deliberada de buenas prácticas, hecha por simplicidad pedagógica. Está documentado en el manifest mismo y en el README, con apuntadores a las soluciones reales (external-secrets-operator, sealed-secrets, Vault, SOPS).

- **Riesgos conocidos y mitigaciones:**
  - **`local-path` no soporta snapshots ni `ReadWriteMany`.** Si el alumno escala a `replicas: 2`, `volumeClaimTemplates` crea otro PVC pero los dos pods van a tener datos divergentes (no es un cluster Postgres replicado, son dos Postgres independientes). Mitigado dejando `replicas: 1` hardcodeado y documentando que escalar requiere un operator.
  - **El init script del `ConfigMap` solo corre si `$PGDATA` está vacío.** Para migraciones futuras (`002_*.sql`, `003_*.sql`) hay que correrlas con un `Job` dedicado o herramienta de migrations (Alembic, Flyway, Liquibase). Documentado explícitamente en el README del Hit #8.
  - **`postgres:16-trixie` puede dejar de existir.** Las imágenes `*-trixie` son tags rolling — Debian trixie eventualmente se va a discontinuar. Mitigación: cuando llegue ese momento, bumpear a `postgres:17-bookworm` o lo que sea LTS en ese punto. Para 2026 está OK.

## Referencias

- StatefulSets — Kubernetes docs: <https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/>
- PostgreSQL official Docker image: <https://hub.docker.com/_/postgres>
- psycopg3 (current generation): <https://www.psycopg.org/psycopg3/docs/>
- CloudNativePG operator (camino de producción): <https://cloudnative-pg.io/>
- Zalando Postgres Operator: <https://github.com/zalando/postgres-operator>
- ADR 0003 (k8s Job + CronJob) — esta decisión extiende ese stack agregando la capa de persistencia consultable.
- Kleppmann — *Designing Data-Intensive Applications*, cap. 2 (modelo relacional vs documento): justifica relacional para queries analíticas sobre histórico temporal.
