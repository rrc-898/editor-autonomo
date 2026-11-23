# Exporta como imagen el fotograma donde está el cabezal (o el timecode de TC) para que Claude pueda MIRARLO.
#   python3 puente/cr.py exec ejemplos/fotograma.py
# Cambia TC y SALIDA antes de ejecutarlo. Funciona desde la página Color (el script la abre y luego vuelve).
import os, tempfile
TC = None                                     # p. ej. "01:00:12:00"; None = donde esté el cabezal
SALIDA = os.path.join(tempfile.gettempdir(), "resolve_fotograma.png")
proj = resolve.GetProjectManager().GetCurrentProject(); tl = proj.GetCurrentTimeline()
antes = resolve.GetCurrentPage(); resolve.OpenPage("color")
if TC:
    tl.SetCurrentTimecode(TC); tl.SetCurrentTimecode(TC)     # a veces la primera llamada no mueve el cabezal
ok = proj.ExportCurrentFrameAsStill(SALIDA)
resolve.OpenPage(antes or "edit")
print(ok, SALIDA, tl.GetCurrentTimecode())
