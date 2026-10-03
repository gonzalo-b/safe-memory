---
title: "Guía Para Probar Memory"
project: memory
type: doc
status: active
created: 2026-10-03
source: codex-desktop
---

# Primera prueba de Memory

La web está en https://memory.lazyagent.ai/. Corre en este Mac y requiere que
el Mac y su conexión permanezcan activos. El acceso pide un usuario propio de
Memory. No hay un botón de login con iCloud ni una importación web de Apple ID.

## Entrar por primera vez

1. Crear el usuario local una sola vez, desde Terminal en este Mac:

   ```sh
   cd /Users/agent/apps/memory-releases/alpha-c9428a6
   '/Users/agent/Library/Application Support/Safe Memory/runtime/venv/bin/python' -m runtime.cli --root '/Users/agent/Library/Application Support/Safe Memory/alpha' create-owner --username owner --name Owner
   ```

   Elegir una contraseña de al menos12 caracteres y repetirla. No se muestra
   al escribir. No enviarla por chat. Si el usuario ya existe, no repetir.
2. Abrir la URL e iniciar sesión como `owner` con esa contraseña.
3. Recorrer Overview, Sources, Photos, Knowledge, Galleries y Debug. La base
   empieza vacía: no contiene los datos sintéticos usados en desarrollo.

## Probar tus fotos

Hay un conector de desarrollo para iPhone, compilado y probado con fixtures,
pero todavía no instalado ni validado en un iPhone real. La cuenta personal
puede quedarse en el iPhone; Memory recibe un vínculo propio y revocable,
no tu contraseña de Apple. El usuario autorizó esta biblioteca como primer
caso real. No se ha efectuado ninguna lectura o importación personal todavía.

Antes de importar, completar el login de Cloudflare en BrowserOS para que el
agente verifique reglas de caché y cabeceras del dominio. La comprobación pública
`no-store`/`DYNAMIC` ya pasó, pero no reemplaza la inspección de todas las reglas.

1. Conectar el iPhone desbloqueado a este Mac y aceptar la confianza del equipo.
   El agente prepara e instala el target de `connectors/ios/SafeMemoryProbe/`
   con Xcode y la firma de desarrollo existente. Cualquier login Apple o
   habilitación de Developer Mode se realiza en la interfaz del propietario.
   No existe todavía una distribución TestFlight/App Store lista para usar.
2. En Sources de la web generar un código de vinculación. En el conector,
   completar la etiqueta/alias, pegar ese código y pulsar `Connect`. Comparar
   la huella completa con la web y confirmar el dispositivo; luego `Check status`.
3. Dar acceso limitado a Fotos y elegir20–30 elementos propios: fotos, un video
   corto y una Live Photo. Es una sugerencia para acotar la primera prueba.
   No se modifica ni elimina nada en Apple Photos.
4. En el conector elegir `Choose sample`, confirmar `Import metadata for this
   exact sample` y pulsar `Import selected metadata`. El adaptador aún no
   distingue con fiabilidad Personal/Shared Library: puede requerir consentimiento
   de posible origen compartido tanto en el conector como en Sources de la web.
   Elegir únicamente elementos propios; no habilitar esas opciones sin revisarlas.
5. Confirmar `Send optimized copies for the last confirmed sample` y pulsar
   `Send optimized copies`. Activar `Allow iCloud downloads for this copy job`
   sólo si se desea probar elementos cuyos archivos deben descargarse de iCloud.
6. En Photos verificar cantidad, fechas, filtros y reproducción de foto/video/
   Live Photo. Si un componente no está disponible, debe verse parcial o pendiente.
7. Pausar/reanudar desde el conector; comprobar que no se duplican los elementos.
   Crear una Gallery, guardar, recargar y verificar que conserva la selección.
8. Después de esa prueba, ampliar el conjunto autorizado y ejecutar
   `Start new authorized scan`; usar `Resume saved index` para reanudar.
   Finalización del índice y copias listas son estados distintos.

## Qué significa dejarlo conectado

El vínculo puede conservarse y revocarse en Sources. El conector debe estar
abierto y ejecutando la operación para importar/reanudar. No hay todavía una
sincronización continua en segundo plano verificada, ni acceso autónomo a iCloud
desde este Mac. El agente puede comprobar el servidor, conteos, errores y
continuidad con el origen autorizado disponible; no puede prometer trabajo
futuro automático sin una tarea o automatización solicitada.

La primera prueba física sigue pendiente. Los resultados de fixtures no prueban
que iCloud, permisos del teléfono o Live Photo funcionen en tu biblioteca real.
