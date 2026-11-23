# Qué hay abierto en Resolve: proyecto, línea de tiempo, pistas, clips y bins.
#   python3 puente/cr.py exec ejemplos/estado.py
pm = resolve.GetProjectManager(); proj = pm.GetCurrentProject()
print("Resolve:", resolve.GetProductName(), resolve.GetVersionString(), "· página:", resolve.GetCurrentPage())
print("Proyecto:", proj.GetName() if proj else None)
if proj:
    print("Ajustes:", {k: proj.GetSetting(k) for k in ("timelineResolutionWidth", "timelineResolutionHeight", "timelineFrameRate")})
    tls = [proj.GetTimelineByIndex(i).GetName() for i in range(1, proj.GetTimelineCount() + 1)]
    print(f"Líneas de tiempo ({len(tls)}):", tls[:40], "…" if len(tls) > 40 else "")
    tl = proj.GetCurrentTimeline()
    if tl:
        print("Actual:", tl.GetName(), "· inicio", tl.GetStartTimecode(), "· duración", tl.GetEndFrame() - tl.GetStartFrame(), "fotogramas")
        for tipo in ("video", "audio", "subtitle"):
            for i in range(1, tl.GetTrackCount(tipo) + 1):
                its = tl.GetItemListInTrack(tipo, i) or []
                print(f"  {tipo} {i} «{tl.GetTrackName(tipo, i)}»: {len(its)} clips", [x.GetName() for x in its[:5]])
        print("Marcadores:", tl.GetMarkers())

    def bins(f, n=0):
        print("  " * n + "📁", f.GetName(), f"({len(f.GetClipList())} clips)")
        for s in f.GetSubFolderList():
            bins(s, n + 1)
    bins(proj.GetMediaPool().GetRootFolder())
