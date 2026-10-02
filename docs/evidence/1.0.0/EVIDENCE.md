---
title: "Alpha V1 Sprint Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# V1.0–V1.4 evidence ledger

Unreleased candidate. VERSION remains 0.1.0. No deployed service, private sample or real-device acceptance yet. Baseline revision 86e71a15bf2bc376b0c517c91797fc9c9bce9189, worktree /private/tmp/memory-v1-foundation, branch codex/memory-v1-0-foundation. Inputs: [INPUTS.md](INPUTS.md). Baseline: [76 aggregate named checks](baseline-gate.md), [59 transport named checks](baseline-contract.md).

G-01: selected committed baseline deliberately; inspected but did not carry original dirty 0.2 changes blindly. Original CONTRACT/store/transport/tests/Graphify/.cody remain unchanged. Graphify query exploration performed, no CodeGraph index, no extraction or inference. Process inspection cannot conclusively establish ownership of old edits; isolation avoids a shared writer.

G-02: architecture/auth/schema proposal awaits GB in the vault's Alpha V1 Technical Delta.md. Host macserver macOS 26.4, Python 3.14.6, SQLite 3.53.2, ~54 GiB available shared space. Existing port 8765 belongs to MindBase. Private runtime and HTTPS deployment not provisioned. No secret printed or source library read.

## Core privacy regression

Command `python3 tests/test_policy_projection.py`: RED exit 1 before fix, 4 passed / 4 failed. Redacted title, entities and source affected matching; redacted source affected source filter. Fixed by projection before caller-controlled filtering. GREEN exit 0: all 8 pass; original row remains unchanged and visible-place redaction compatibility preserved. This is fixture evidence of part of F2-03, not full F2 acceptance. Implementation SHA pending commit.

## Acceptance tracking

| ID | State | Required outcome |
|---|---|---|
| G-01 | pending | Baseline real, titularidad del dirty diff, inputs/hash y named tests registrados sin perder trabajo previo. |
| G-02 | pending | Delta técnico aprobado donde hace falta, servidor/destino privado/capacidad y recovery verificados; sin stack o despliegue inventado. |
| F0-01 | pending | App real inicia y es accesible por owner autorizado desde el servidor previsto; acceso ajeno/sin sesión denegado. |
| F0-02 | pending | Persistencia real sobrevive restart/reload; fixtures aisladas y visibles como tales. |
| F0-03 | pending | Un Vault Photos por owner creado automáticamente, retry/reconnect sin duplicado ni Grant implícito. |
| F0-04 | pending | Navegación/onboarding adoptan HTML+DS y muestran estados reales; misiones posteriores no simulan éxito. |
| F0-05 | pending | Debug muestra health/operaciones/audit reales y aplica las mismas restricciones de acceso. |
| F0-06 | pending | Gates previos preservados por nombre, pruebas negativas y recuperación básica pasan. |
| F1-01 | pending | Ruta iPhone-only probada en dispositivo real autorizado, con capacidades/versión/limitaciones y no mutación registradas. |
| F1-02 | pending | Full/limited/denied/revoked y registro owner/device seguros; muestra no presentada como whole library. |
| F1-03 | pending | Reciente primero y backfill reanudable; índice/medios/cobertura/exclusiones/freshness separados y honestos. |
| F1-04 | pending | Replay/crash/retry conservan IDs/revisiones, no duplican hechos y no dañan generación previa. |
| F1-05 | pending | Fotos, video y Live still/motion/audio importan bajo política de copias optimizadas; missing source/cloud-only explícitos. |
| F1-06 | pending | Hidden default y restricción tras detección pasan en UI/Blocks/caches/medios/Artifacts; retención restringida conservada. |
| F1-07 | pending | Shared Library y Shared Albums separados, opt-in y provenance verificados; terceros no se atribuyen al owner. |
| F1-08 | pending | Payload raw autorizado, campos ausentes, time basis y clasificación conservados; Debug retry funciona sin bypass. |
| F2-01 | pending | Travel Log, Countries/Cities, Trips, period statistics y On This Day producen resultados determinísticos con evidencia. |
| F2-02 | pending | Fecha/rango/año/ocasión y unknowns responden correctamente, incluidas N ocurrencias con años desconocidos; sin inventar continuidad, cumpleaños o ubicación. |
| F2-03 | pending | Permisos antes de matching/agregación/discovery, redacciones y ventanas aplicadas a Blocks/evidence/cache; regresiones del baseline cerradas. |
| F2-04 | pending | Rebuild publica generación coherente y conserva la anterior ante fallo; latencias/recursos medidos con presupuesto explícito. |
| F2-05 | pending | Detección same-day/overnight y exclusión de commuting probadas con fixtures conocidas. |
| F2-06 | pending | Habitual areas múltiples/históricas, inferencia vs confirmación y correcciones persistentes funcionan. |
| F2-07 | pending | Renombrar, editar fechas, merge, split y creación manual sobreviven reimport/rebuild sin cambiar source. |
| F2-08 | pending | People limitado a metadata realmente importada; ausencia no genera falsas features ni bloquea entrega. |
| F3-01 | pending | Biblioteca/filtros/viewer funcionan sobre medios reales autorizados, con fecha/lugar/tipo y evidencia disponibles. |
| F3-02 | pending | Foto, video y Live motion/audio se reproducen desde copias servidor con iPhone offline. |
| F3-03 | pending | Original owner-requested tiene request idempotente, waiting/retry/ready real y retención correcta. |
| F3-04 | pending | Todos los componentes/URLs/Range/posters/thumbnails respetan owner y permisos actuales; nada público por accidente. |
| F3-05 | pending | Formatos/capacidad/errores se prueban y declaran; un play ficticio o still-only no pasa. |
| F4-01 | pending | Crear Gallery Artifact privado desde selección autorizada, guardar y listar sin agente/Plugin framework obligatorio. |
| F4-02 | pending | Reabrir tras restart conserva ID/título/media/edits/exclusiones; agregar/quitar funciona sin mutar Photos. |
| F4-03 | pending | Retry/recomposición/concurrencia no pierden exclusiones ni correcciones; fallo conserva última revisión coherente. |
| F4-04 | pending | Lineage/evidence links seguros y permisos actuales se aplican también a outputs persistidos y cache. |
| F4-05 | pending | Rendering seguro y Debug de Artifact con operación real, sin publicación/email/World Map anticipados. |
| Q-01 | pending | Recorrido integrado real F0→F1→F2→F3→F4 pasa en el mismo candidato, incluida muestra device real. |
| Q-02 | pending | Browser QA de app real en 1440×900/390×844 y ancho 320 px, System/light/dark, estados/keyboard, reduced motion/zoom 200%, sin errores bloqueantes ni fuentes remotas; CSS completo validado. |
| Q-03 | pending | Restore aislado y fallos de audit/ingest/rebuild/save pasan sin pérdida de edits ni resurrección de acceso. |
| Q-04 | pending | `tests/run_all.py`, `tests/test_stub.py`, tests relevantes/E2E y `git diff --check` verdes; sin defectos críticos/altos conocidos. |
| Q-05 | pending | Cada criterio tiene evidencia sanitizada de revisión correcta; docs de conducta, VERSION y CHANGELOG consistentes con lo realmente entregado. |
| Q-06 | pending | PRs autorizados entregados según checks exact-SHA, merge confirmado y árbol integrado verificado; recibos distinguen verificación local/push/merge/deployment. |
| Q-07 | pending | `PROGRESS.md` final y digest MindBase registran alcance entregado hasta V1.4, siguientes V1.5–V1.10 y pendientes reales sin llamar a este sprint «V1 completa». |
