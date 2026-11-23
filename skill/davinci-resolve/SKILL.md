---
name: davinci-resolve
description: Editar en DaVinci Resolve desde Claude Code a través del puente del Editor autónomo (funciona también en la versión gratuita) y bajar el material de la nube con rclone (Google Drive, OneDrive, SharePoint). Usar cuando el usuario pida montar, cortar, etalonar, poner textos o subtítulos, revisar o exportar un vídeo, documental, reel o proyecto en DaVinci Resolve, o descargar el metraje de una carpeta en la nube.
---

# Editar en DaVinci Resolve con el puente

Claude no ve la pantalla de Resolve: le da órdenes por su API de scripting a través de un puente local y comprueba el
resultado exportando fotogramas o renders. Todo se hace sobre la sesión VIVA de Resolve, con el proyecto que tenga abierto
la persona.

## 1. Conectar
1. Resolve abierto, con un proyecto. Si no está, pedírselo a la persona (o abrir el proyecto que diga).
2. La persona lanza el puente una vez por sesión: **Área de trabajo › Secuencias de comandos › editor_autonomo_puente**
   (Workspace › Scripts). Queda escuchando; la interfaz de Resolve sigue funcionando. Si no aparece en el menú, hay que
   reiniciar Resolve (lee la carpeta de scripts al arrancar).
3. Comprobar: `{{CR}} ping` → «DaVinci Resolve 2x.x». Si dice que nadie escucha, el puente no está lanzado.
4. Situarse: `{{CR}} exec {{EJEMPLOS}}/estado.py` (proyecto, líneas de tiempo, pistas, clips, marcadores, bins).

Órdenes: `{{CR}} eval "expresión"` para algo corto; `{{CR}} exec script.py` para todo lo demás (escribir el script en un
archivo temporal y ejecutarlo). Dentro ya existen `resolve`, `fusion` y `bmd`. Lo que imprime el script vuelve a Claude.
Un script largo bloquea el puente hasta que termina (render, importaciones grandes): es normal.

## 2. Antes de tocar nada
- **Leer la documentación oficial de ESTA instalación**: `{{API_README}}` (lista completa de funciones de la versión instalada;
  hay ejemplos en la carpeta `Examples/` de al lado). No inventar funciones: si no está en el README, no existe.
- Preguntar lo que no esté claro del encargo (duración, formato 16:9 o vertical, tono, música, entrega) y proponer un plan
  antes de montar algo largo.
- **Nunca destruir**: no borrar líneas de tiempo, clips ni bins de la persona. Trabajar en una línea de tiempo nueva o en un
  duplicado (`DuplicateTimeline`) y pedir permiso antes de borrar o sobrescribir. Guardar al acabar cada fase:
  `resolve.GetProjectManager().SaveProject()`.

## 3. Recetas comprobadas (Resolve 21, Linux, versión gratuita)
- Proyecto, media pool y línea de tiempo:
  `pm = resolve.GetProjectManager(); proj = pm.GetCurrentProject(); mp = proj.GetMediaPool()`
  `tl = proj.GetCurrentTimeline()` · por nombre: `{proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)}`
- Importar: `mp.ImportMedia([rutas])` devuelve los MediaPoolItem. Organizar con `mp.AddSubFolder(root, "nombre")` y
  `mp.SetCurrentFolder(carpeta)` ANTES de importar.
- Montar al fotograma: `mp.AppendToTimeline([{"mediaPoolItem": it, "startFrame": a, "endFrame": b, "mediaType": 1,
  "trackIndex": 1, "recordFrame": f}])`. `endFrame` es EXCLUSIVO. `mediaType` 1 = solo vídeo, 2 = solo audio. Los
  fotogramas de origen van en los fps del clip: si el clip es de 60 y la línea de tiempo de 30, usar `ceil(n·fps/30)`.
- Sustituir un plano: `tl.DeleteClips([item], False)` y volver a añadir en su `recordFrame`.
- Recorte, zoom, giro: `item.SetProperty("ZoomX", 1.2)`, `"ZoomY"`, `"Pan"`, `"Tilt"`, `"RotationAngle"`, `"CropLeft"`…
- Cámara lenta: `it.SetClipProperty("FPS", "30")` en un clip de 50/60 fps (hacerlo DESPUÉS de `ReplaceClip`, que lo resetea).
- Marcadores: `tl.AddMarker(frame, "Blue", "nombre", "nota", 1)` / `tl.GetMarkers()` — útiles para que la persona revise.
- Títulos Text+: `InsertFusionTitleIntoTimeline` devuelve None y no sirve para colocarlos. Lo fiable: tener una línea de
  tiempo «plantilla» con un Text+ ya puesto en V2 (hecha a mano una vez, o importada de un `.drt` con
  `mp.ImportTimelineFromFile(ruta)`), duplicarla y editar el título:
  `comp = item.GetFusionCompByIndex(1); tp = comp.FindTool("Template")`, luego `tp.SetInput("StyledText", "…")`, `"Font"`,
  `"Style"`, `"Size"`, `"Center"` ({1: x, 2: y, 3: 0}, 0-1 desde abajo a la izquierda). Sombra: `Enabled3` = 1, `Alpha3`, `Softness3`.
  Texto que cambia en el tiempo: `tp.ConnectInput("StyledText", comp.BezierSpline())` y `tp.SetInput("StyledText", txt, frame)`.
  Antes de conectar una spline poner `comp.CurrentTime = 0` y claves explícitas al principio y al final.
- **Texto gris con gestión de color**: con «DaVinci YRGB Color Managed» y Output DRT «DaVinci», el blanco 1,0 del Text+ sale a
  188/255. Poner `Red1`, `Green1`, `Blue1` a 10 da 254. Medir siempre el render.
- Fuentes en Fusion: solo ve las carpetas del sistema; si falta una fuente, instalarla en el sistema y reiniciar Resolve.
  El nombre real se consulta con `fusion.FontManager.GetFontList()`.
- Color por clip (página Color): `item.SetCDL({"NodeIndex": "1", "Slope": "1 1 1", "Offset": "0 0 0", "Power": "1 1 1",
  "Saturation": "1"})`. La API no crea nodos: se aplica un grade guardado con `item.GetNodeGraph().ApplyGradeFromDRX(ruta, 0)`
  (un .drx exportado con GrabStill + ExportStills) y luego se ajusta cada nodo con SetCDL. LUT: `graph.SetLUT(nodo, "carpeta/x.cube")`
  con el LUT en la carpeta LUT de Resolve y `proj.RefreshLUTList()`.
- HDR del iPhone (HLG): en un proyecto con gestión de color, declarar el clip `it.SetClipProperty("Input Color Space", "Rec.2100 HLG")`.
  Si se lee como Rec.709 sale gris, lavado y con negros lechosos.
- Render: `proj.SetCurrentRenderFormatAndCodec("mov", "ProRes422HQ")`, `proj.SetRenderSettings({"TargetDir": carpeta,
  "CustomName": nombre, "SelectAllFrames": False, "MarkIn": a, "MarkOut": b, "ExportVideo": True, "ExportAudio": True})`,
  `j = proj.AddRenderJob(); proj.StartRendering([j], isInteractiveMode=False)` y esperar con
  `while proj.IsRenderingInProgress(): time.sleep(1)`. `AddRenderJob` devuelve "" si no le gusta la carpeta (que exista y
  esté en tu carpeta de usuario). Los ajustes se QUEDAN para el siguiente render: indicar siempre ExportAudio.
- Mirar el resultado: `{{EJEMPLOS}}/fotograma.py` exporta el fotograma del cabezal como PNG (`ExportCurrentFrameAsStill`, desde la
  página Color; `SetCurrentTimecode` a veces hay que llamarlo dos veces). Para revisar un montaje entero: renderizarlo y sacar
  fotogramas con ffmpeg a varios tiempos, y mirar las imágenes.
- Clicar en la interfaz (solo Linux/X11, opcional): `puente/xclick.py click X Y` para lo que la API no hace (p. ej. lanzar el puente).

## 4. Trampas conocidas
- **Resolve gratuito en Linux no lee H.264/H.265 ni AAC** (los vídeos del móvil): convertirlos antes con ffmpeg a DNxHR o
  ProRes + PCM y trabajar con esos .mov. En Windows y macOS sí los lee. Para exportar MP4 en Linux: render ProRes y
  pasarlo a H.264 con ffmpeg.
- Las funciones `Insert…IntoTimeline` meten en la pista de destino y desplazan lo que hay detrás: para colocar al fotograma
  usar `AppendToTimeline` con `recordFrame`.
- `SetTrackEnable` no hace nada en una pista vacía: activar después de meter clips y comprobar con `GetIsTrackEnabled`.
- Si el puente deja de responder tras reiniciar Resolve: `{{CR}} stop` (o cerrar Resolve) y volver a lanzarlo desde el menú.
- Los archivos que lee el script dentro de Resolve: abrir con `encoding="utf-8"`.

## 5. Bajar el material de la nube (rclone)
Herramienta: `{{NUBE}}`. Solo lectura: nunca sube, borra ni sincroniza.
- Ver remotos: `{{NUBE}} remotos`. Si no hay, la persona crea uno con `rclone config` (abre el navegador para iniciar
  sesión; es suyo, Claude no introduce contraseñas). Tipos: `drive` (Google Drive; mejor con permiso solo lectura),
  `onedrive` (OneDrive y SharePoint: al configurarlo, elegir la biblioteca del sitio de SharePoint), `dropbox`…
- Mirar antes de bajar: `{{NUBE}} ver REMOTO:carpeta` (lista y tamaño total). Enlace de una carpeta de Google Drive
  (…/folders/ID): `--carpeta-id ID`; carpeta «Compartido conmigo»: `--compartido`.
- Bajar: `{{NUBE}} bajar REMOTO:carpeta DESTINO` comprueba que cabe (deja 10 GB libres; `--margen`), copia con reintentos y
  verifica con `rclone check`. Si se corta, la misma orden sigue donde iba. Solo una parte: `--incluir "*.mov"`.
- Google Drive admite dos archivos con el mismo nombre en una carpeta y rclone solo baja uno («Duplicate object»): avisar a
  la persona y bajarlos por ID (`rclone backend copyid REMOTO: ID "nombre (2).ext"`).
- Metraje grande: preguntar antes de bajar decenas de GB y no llenar el disco.

## 6. Forma de trabajar
- Un plan corto antes de montar; después, fase a fase, enseñando fotogramas o renders de control.
- Medir en vez de suponer: duración, cortes, niveles (negro/blanco, % quemado), sonoridad del audio (`ffmpeg -af ebur128`).
- Al acabar: guardar el proyecto, decir qué línea de tiempo y qué render se han creado, y qué queda pendiente.
