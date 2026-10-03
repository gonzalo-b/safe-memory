---
title: "Alpha V1 Through V1.4 Acceptance Ledger"
project: memory
type: doc
status: blocked
created: 2026-10-03
source: codex-desktop
---

# Matriz de aceptación — 41 criterios G/F0–F4/Q

Inventario integrado iniciado sobre85606c5 y actualizado con los recibos de entrega en [EVIDENCE.md](EVIDENCE.md). Cada recibo identifica su código probado; los commits de evidencia posteriores se comparan por árbol de implementación. Los IDs y el alcance provienen del [goal original](/Users/agent/.codex/attachments/e73a2170-3d03-448b-9d6c-9d3692ff44c6/pasted-text-1.txt).

**Implementado y probado con fixtures no equivale a aceptación con iPhone, muestra del owner o servidor previsto. Ninguna fila convierte esas dependencias externas en un pass.** «Sin gap local identificado» describe esta revisión acotada, no una certificación de ausencia de defectos.

## Evidencia de referencia

Los recibos históricos indican su revisión propia; no se presentan como ejecuciones nuevas sobre el candidato final.

- **B**: [baseline y titularidad](../1.0.0/EVIDENCE.md), [inputs/hash](../1.0.0/INPUTS.md).
- **F0**: [runtime, autenticación y recovery](../v1.0-runtime/EVIDENCE.md).
- **I**: [pairing, metadata y permisos](../v1.1-ingestion/EVIDENCE.md), [ingesta progresiva/capacidad](../v1.1-progressive/EVIDENCE.md).
- **N**: [probe nativo](../v1.1-probe/EVIDENCE.md), [conector progresivo](../v1.1-native-progressive/EVIDENCE.md). Build unsigned y harnesses Swift; no prueba física ni runtime de simulador.
- **K**: [conocimiento, correcciones y benchmark](../v1.2-knowledge/EVIDENCE.md).
- **M**: [medios privados](../v1.3-media/EVIDENCE.md).
- **O**: [originales, capacidad y restore integrado](../v1.3-originals/EVIDENCE.md).
- **A**: [Artifacts](../v1.4-artifacts/EVIDENCE.md), [UI/lineage/keyboard/zoom y límites de QA](../../../web/ARTIFACTS.md).
- **Final**: [gate373/0](memory-final-integrated-gate.log), [contrato67/0](memory-final-integrated-contract.log), [browser220/220](memory-final-integrated-matrix.log), [unit12/12](memory-final-integrated-unit.log), [build](memory-final-integrated-build.log), [TypeScript](memory-final-integrated-types.log), [DS](memory-final-integrated-ds.log). Recibos canónicos conservados en esta carpeta; no equivalen a muestra real.
- **Actual sintético final**: Next→Python sin mocks: [original2/2](memory-final-original-runtime.log), [knowledge2/2](memory-final-knowledge-runtime.log), [progressive2/2](memory-final-progressive-runtime.log), [Gallery JPEG2/2](memory-final-gallery-media-runtime.log), [Gallery prepare2/2](memory-final-artifact-prepare.log), [Gallery restart2/2](memory-final-artifact-restart.log). El integrador confirmó restart PID61587→68571 conservando código/store. Fuentes sintéticas retenidas y restringidas; no borradas.
- **Media final**: [RED2/2 conservado](memory-final-media-runtime.log), [GREEN2/2 con audio sink de QA](memory-final-media-runtime-audio-sink.log). El integrador diagnosticó freeze0.02322s también con dataURL aislado por salida de audio del host. Chromium QA usa `--disable-audio-output`, conservando `element.muted=false`, bytes de audio decodificados y avance de currentTime. Prueba decodificación/reproducción sintética; no sonido audible en hardware. No se oculta el RED ni se presenta el flag como cambio del producto.

## Matriz

| ID | Implementación / evidencia disponible | Pendiente para aceptar el criterio completo |
|---|---|---|
| G-01 | Baseline, dirty diff ajeno, inputs/hash y nombres previos registrados. B; Final. | Sin gap local identificado; conservar trazabilidad en recibo final. |
| G-02 | Delta frontend/backend aprobado; loopback privado y recovery implementados. F0/O. | Verificar destino previsto, acceso privado y capacidad operativa. Cloudflare read-only rechazado por revisión automática; autorización explícita del usuario pendiente. |
| F0-01 | Login, cookie/sesión, CSRF y denegaciones ejecutados en app real local. F0; actual sintético final. | Acceso del owner desde servidor previsto y prueba externa sin sesión/owner ajeno. |
| F0-02 | Reload/sesión y persistencia local; Gallery sobrevive restart real del mismo store. F0/A; prepare+restart finales2/2. | Persistencia del despliegue previsto dentro del recorrido externo. Fixtures siguen identificadas como sintéticas. |
| F0-03 | Confirmación explícita crea/reutiliza conexión y Vault; retries/reconnect únicos, sin Grant implícito. I/Final. | Verificación con registro del iPhone autorizado; no gap local identificado. |
| F0-04 | Navegación/onboarding DS y estados reales; no éxitos ficticios; fuentes/iconos locales. Final220/12/DS. | Recorrido del owner en despliegue/dispositivo. |
| F0-05 | Health, operaciones/audit y Debug reales protegidos. F0/I/K/A; actual sintético final. | Verificar operaciones del entorno previsto; no gap local identificado. |
| F0-06 | Gates preservados, pruebas negativas y recovery local. Final373/67; O. | Sin gap local identificado; mantener nombres y exact-SHA en recibo de entrega. |
| F1-01 | Conector iPhone-only implementado, build unsigned y harnesses nativos. N. | **No aceptado físicamente:** devicectl muestra0 dispositivos. Faltan iPhone autorizado, firma/trust y prueba de no mutación. |
| F1-02 | Pairing/confirm/revoke y full/limited/denied/revoked implementados y probados sintéticamente. I/N. | Permisos reales de PhotoKit y registro del owner; muestra no es whole library. |
| F1-03 | Reciente primero, backfill/cursor/reanudación y cobertura separada. I/N; progressive final2/2. | Backfill real con teléfono/red/cloud; medir cobertura efectiva sin extrapolar fixtures. |
| F1-04 | IDs/revisiones, replay/crash/retry y publicación atómica cubiertos. I/K/N/Final. | Ejercicio físico de interrupción/reanudación; no gap local identificado. |
| F1-05 | Transferencia optimizada y componentes photo/video/Live; estados missing/cloud/partial explícitos. M/N/O. | Importar muestra física con still/motion/audio y formatos reales. |
| F1-06 | Hidden default, revocación/current-policy en metadata/Blocks/medios/Artifacts; raw restringido retenido. I/K/M/A/Final. | Detección real de cambio Hidden en PhotoKit y propagación end-to-end. |
| F1-07 | Shared Library y Shared Albums separados, consentimientos explícitos y provenance conservador. I/N/K. | Verificar categorías y provenance en assets reales autorizados; no atribuir terceros al owner. |
| F1-08 | Raw autorizado, campos ausentes/offset original y clasificación; Debug retry sin bypass. I/N; progressive final2/2. | Contrastar payload expuesto por dispositivo/versión reales; sin inventar offset faltante. |
| F2-01 | Capacidades determinísticas y evidencia autorizada implementadas. K; knowledge final2/2. | Contrastar muestra real conocida; geografía solo explícitamente importada. |
| F2-02 | Fecha/rango/año/ocasión N, unknowns y29feb exacto cubiertos; no continuidad inventada. K/Final. | Verificación con ejemplos reales acordados; no gap local identificado. |
| F2-03 | Política/scope/revisión antes de matching/agregación/evidence; stale UI se limpia. K/Final; knowledge final2/2. | Repetir restricciones de muestra real; no gap local identificado. |
| F2-04 | Rebuild atómico/fallo conserva generación;100k medidos. K. | Presupuesto local declarado antes de medir:600ms/30s/256MiB/384MiB. Rerun100k en2fc917a pasó: máximo p95281.14ms, rebuild13.108s, RSS156.64MiB/store238.49MiB. Recibo canónico adjunto y misses anteriores retenidos; queda medir muestra/red reales. |
| F2-05 | Same-day/overnight, gaps y commuting histórico confirmado cubiertos por fixtures. K/Final. | El criterio de fixtures tiene prueba; calibración sobre muestra real aún pendiente. |
| F2-06 | Áreas múltiples/históricas, inferencia/confirmación y ediciones persistentes. K; knowledge final2/2. | Contrastar semántica con áreas de la muestra autorizada; no gap local identificado. |
| F2-07 | Manual/rename/fechas/merge/split con IDs durables, revisiones y reimport/rebuild sin escribir Source. K/O/Final. | Recorrido de corrección del owner; no gap local identificado. |
| F2-08 | People limitado a metadata importada y ausencia honesta; no reconocimiento inventado. K/Final. | Documentar disponibilidad efectiva del dispositivo; ausencia no bloquea entrega. |
| F3-01 | Biblioteca/viewer, día/período/tipo/lugar/trip/colección y metadata/evidence integrados. API aplica matching autorizado antes de paginar.10tests nuevos,56UI de metadata y actual2/2 con33assets prueban intersección24+6 y trip3; restricción produce404/sin resultados. [API](../alpha-v1-3-photos-filters-api/EVIDENCE.md), [UI](../v1.3-filters-ui/EVIDENCE.md), [actual](memory-filters-real-runtime.log). | Verificar muestra real; brecha local de filtros cerrada. |
| F3-02 | Copias servidor independientes del uploader; JPEG y playback video/Live/audio decodificado sintéticos2/2, audio sink QA documentado. M/A; actual final. | Probar video/Live/audio audible con iPhone físico offline. El GREEN headless no establece salida audible del hardware. |
| F3-03 | Original idempotente waiting/failure/retry/ready, recursos exactos/hash/retención; actual final2/2. O. | Solicitud/export real PhotoKit/iCloud, teléfono offline→online y formatos del owner. |
| F3-04 | Cookies, rutas exactas, Range/no-store y autorización/audit en cada body, incluso tras headers. M/O/Final. | Verificar configuración externa sin URLs públicas/caché que amplíe permisos; no gap local identificado. |
| F3-05 | Límites/errores explícitos; benchmark64/256MiB y fixtures JPEG/H264/AAC. M/O. | HEIC/HEVC/RAW/Live reales y capacidad/red del destino sin extrapolar bytes sintéticos. |
| F4-01 | Gallery privada desde Photos o snapshot de trip; guarda/lista sin Plugins/agente. A; actual final. | Muestra autorizada real; no gap local identificado. |
| F4-02 | ID/título/layout/order/cover/edits/exclusiones persisten; add/remove sin mutar Photos. A; restart final2/2, JPEG final2/2 separado. | Repetir recorrido con medios de muestra real; no gap local identificado. |
| F4-03 | Retry estable,409, recomposición/exclusiones, concurrencia y rollback atómico. A/Final; restart final2/2. | Sin gap local identificado; mantener prueba en candidato de entrega. |
| F4-04 | Lineage seguro visible, evidencia/current-policy en detalle/lista/Debug; revalidación completa antes de abrir miembro. A/Final; JPEG/restart finales. | Verificación con permisos reales; no gap local identificado. |
| F4-05 | Texto seguro, composición grid/story mínima y visor privado; Debug de operaciones reales. A/Final. | Sin gap local identificado. Sin publicación/email/World Map ni afirmación de compositor avanzado. |
| Q-01 | Integraciones locales reales, con fixtures, de F0–F4 sobre candidato final. | **No aceptado:** falta mismo recorrido con dispositivo/muestra real y destino previsto; filtros F3-01 ya cerrados localmente. |
| Q-02 |220 casos,1440×900/390×844/320px, light/dark/System, keyboard/reduced-motion, DS/CSS y fuentes locales. A/Final. |Usabilidad ampliada200% se midió con CSS zoom (foco, bounds y scroll), no con el menú nativo del navegador. Inputs date se poblaron mediante el navegador; no se afirma edición segmentada exclusivamente por teclado. QA real del iPhone permanece pendiente. |
| Q-03 | Restore integrado retiene trip/Gallery/copia/original y mantiene quarantine; fallos audit/ingest/rebuild/save. O/Final. | Recovery operativo en destino; sin gap local identificado en recuperación aislada. |
| Q-04 | Gate integrado383/0, contrato67/0, matrix240/240, unit13/build/types/DS. Final EVIDENCE identifica exact-SHA/equivalencias. Audio sink QA conserva todos losasserts; RED236/4 y GREEN240 retenidos. | Sin gap local de tests conocido; mantener evidencia de revisión y repetir el recorrido físico cuando esté disponible. |
| Q-05 | Evidencia histórica sanitizada, docs por comportamiento y VERSION0.1.0 honesto como no liberado. B–A/Final. | Ledger41 y docs/CHANGELOG se consolidan con recibo final de revisión; VERSION permanece0.1.0 porque el despliegue/conector real aún no se aceptaron. |
| Q-06 | PRs previos con recibos; integrador confirma PR15 F4 merged `b5fbd5726435b81525bc22e22e9b916cc971729c` (head probado7d58289,345/67,196UI/11unit). | PR16 originals29461e4 merged f14b6b544db29ffdc1003e77504397e780e80caf, exact373/67 y árbol idéntico. PR17 mergedc9428a6 y build durable verificado: [DELIVERY.md](DELIVERY.md). Código integrado; despliegue externo pendiente. |
| Q-07 | Checkpoints parciales conservan distinción implementación/fixture/deployment. | PROGRESS conserva el checkpoint final. El digest de cierre registra el recibo real de merge/build y bloqueos; se consulta junto con EVIDENCE. Alcance hastaV1.4; no «V1 completa». |

## Pasos externos inevitables y cierres locales

1. **Acceso al destino:** responder la autorización explícita pendiente para inspección Cloudflare de solo lectura. La revisión automática rechazó esa acción; no eludir el bloqueo. Después verificar ruta existente, privacidad, owner, capacidad y recovery, sin inventar despliegue.
2. **Dispositivo/firma:** conectar/desbloquear un iPhone autorizado, establecer trust/Developer Mode y firma válida con el equipo elegido por el owner. devicectl0devices impide sustituir esto con más fixtures o builds unsigned.
3. **Owner y muestra:** provisionar owner de producción por un canal privado; autorizar una muestra30–100 assets y permisos Photos apropiados. Registrar versiones/capacidades, full/limited/denied/revoked, Hidden/shared separados, unknowns y que nada se modificó en Photos. No pedir contraseñas en chat ni usar biblioteca personal sin autorización.
4. **Recorrido real:** ejecutar F0→F4 sobre una misma revisión con esa muestra; foto/video/Live audio, offline, cloud/missing, original waiting→retry→ready, reanudación, evidencia/correcciones, Gallery y restricción/restart. Conservar evidencia sanitizada y límites de formatos/cobertura; registrar la verificación end-to-end, sin imponer una nueva aprobación humana del milestone.
5. **Cierre local aún posible sin esa dependencia:** Filtros F3-01 cerrados con prueba real sintética; RED→GREEN media/audio y benchmarks consolidados. Recibos finales de entrega y build durable se agregan en EVIDENCE.md; sigue pendiente únicamente la aceptación externa descrita. Gallery restart ya pasó. Esta matriz no impide continuar esos cierres mientras se esperan dispositivo y acceso.

No hay criterio marcado como aceptación externa completa por sustitución sintética. Los resultados finales se deben actualizar si las correcciones cambian el candidato SHA.

