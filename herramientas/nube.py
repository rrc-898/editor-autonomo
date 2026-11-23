#!/usr/bin/env python3
"""Bajar material de la nube (Google Drive, OneDrive, SharePoint, Dropbox…) con rclone, SOLO LECTURA.

    nube.py remotos                                    remotos configurados en rclone
    nube.py ver REMOTO:ruta [opciones]                 qué hay y cuánto ocupa (no baja nada)
    nube.py bajar REMOTO:ruta DESTINO [opciones]       copia a DESTINO, comprueba espacio antes y verifica después

Opciones (Google Drive):
    --carpeta-id ID      entra directamente en la carpeta del enlace (…/folders/ID); vale para carpetas compartidas
    --compartido         busca en «Compartido conmigo»
Otras:
    --incluir PATRÓN     solo lo que encaje, p. ej. "*.mov" (se puede repetir)
    --margen GB          espacio libre que debe quedar en el disco tras bajar (10 por defecto)

Nunca borra ni modifica nada en la nube: usa `rclone copy` (no `sync`) y `rclone check --one-way`.
Los remotos se crean una vez con `rclone config` (lo hace la persona: pide iniciar sesión en el navegador).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys


def rclone(*args, capturar=True):
    if not shutil.which("rclone"):
        sys.exit("No encuentro rclone. Instálalo: https://rclone.org/install/ (brew install rclone · winget install Rclone.Rclone)")
    r = subprocess.run(["rclone", *args], capture_output=capturar, text=True)
    if capturar and r.returncode != 0:
        sys.exit(r.stderr.strip() or f"rclone {' '.join(args)} falló")
    return r


def flags(a):
    f = []
    if a.carpeta_id:
        f += ["--drive-root-folder-id", a.carpeta_id]
    if a.compartido:
        f += ["--drive-shared-with-me"]
    for p in a.incluir or []:
        f += ["--include", p]
    return f


def gb(n):
    return f"{n / 1e9:.2f} GB"


def cmd_remotos(a):
    print(rclone("listremotes", "--long").stdout.strip() or "No hay remotos. Créalos con: rclone config")


def tamano(a):
    j = json.loads(rclone("size", "--json", a.origen, *flags(a)).stdout)
    return j.get("count", 0), j.get("bytes", 0)


def cmd_ver(a):
    print(rclone("lsf", "-R", "--format", "sp", "--separator", "  ·  ", a.origen, *flags(a)).stdout.rstrip())
    n, b = tamano(a)
    print(f"\n{n} archivos, {gb(b)}")


def cmd_bajar(a):
    n, b = tamano(a)
    os.makedirs(a.destino, exist_ok=True)
    libre = shutil.disk_usage(a.destino).free
    print(f"{n} archivos, {gb(b)} · libre en destino {gb(libre)}", flush=True)
    if b + a.margen * 1e9 > libre:
        sys.exit(f"No cabe dejando {a.margen} GB libres. Libera espacio, elige otra carpeta o baja una parte con --incluir.")
    # Drive puede tener nombres repetidos en la misma carpeta: rclone solo bajaría uno; se avisa en la salida
    r = rclone("copy", a.origen, a.destino, *flags(a), "--progress", "--transfers", "4", "--retries", "5",
               "--low-level-retries", "10", capturar=False)
    if r.returncode != 0:
        sys.exit("La copia terminó con errores: vuelve a lanzar la misma orden (lo ya bajado se salta).")
    c = subprocess.run(["rclone", "check", "--one-way", a.origen, a.destino, *flags(a)], capture_output=True, text=True)
    print((c.stderr.strip().splitlines() or [""])[-1])
    print("Verificado: todo bajado y con el mismo tamaño/hash." if c.returncode == 0 else
          "OJO: hay diferencias (archivos que faltan o distintos). Vuelve a lanzar la copia y revisa los nombres repetidos.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("remotos")
    for nombre in ("ver", "bajar"):
        p = sub.add_parser(nombre)
        p.add_argument("origen")
        if nombre == "bajar":
            p.add_argument("destino")
            p.add_argument("--margen", type=float, default=10)
        p.add_argument("--carpeta-id"); p.add_argument("--compartido", action="store_true")
        p.add_argument("--incluir", action="append")
    a = ap.parse_args()
    {"remotos": cmd_remotos, "ver": cmd_ver, "bajar": cmd_bajar}[a.cmd](a)


if __name__ == "__main__":
    main()
