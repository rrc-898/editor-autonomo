"""Puente del Editor autónomo para DaVinci Resolve (también la versión gratuita).

Resolve free no acepta scripting externo (scriptapp("Resolve") devuelve None fuera de la app), pero sí ejecuta los
scripts del menú Área de trabajo › Secuencias de comandos (Workspace › Scripts). Este script, lanzado desde ahí, abre un
servidor TCP en 127.0.0.1 (puerto de config.json, 51708 por defecto) protegido con un token, y ejecuta el Python que le
manda cr.py con `resolve`, `fusion` y `bmd` ya definidos.

install.sh lo COPIA (no enlace: Resolve no sigue bien los enlaces) en
~/.local/share/DaVinciResolve/Fusion/Scripts/Utility/  (Linux)
Se queda en primer plano a propósito: Resolve corta los hilos en cuanto el script termina. La interfaz sigue respondiendo.
"""
import contextlib
import io
import json
import os
import socket
import traceback

BASE = os.path.expanduser("~/.config/editor-autonomo")
HOST = "127.0.0.1"
try:
    PORT = int(json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8")).get("puerto", 51708))
except Exception:
    PORT = 51708
LOG = os.path.join(BASE, "puente.log")


def _log(txt):
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(txt + "\n")


def _resolve():
    g = globals()
    if g.get("resolve"):
        return g["resolve"]
    if g.get("app"):
        return g["app"].GetResolve()
    return g["bmd"].scriptapp("Resolve")


def _ejecutar(code, ns):
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                res = eval(compile(code, "<claude>", "eval"), ns)
            except SyntaxError:
                exec(compile(code, "<claude>", "exec"), ns)
                res = ns.pop("_", None)
        return {"ok": True, "out": out.getvalue(), "result": repr(res) if res is not None else None}
    except Exception:
        return {"ok": False, "out": out.getvalue(), "err": traceback.format_exc()}


def _atender(conn, token, ns):
    with conn:
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = conn.recv(65536)
            if not chunk:
                return
            buf += chunk
        try:
            req = json.loads(buf.decode())
        except ValueError:
            return
        try:   # el objeto inyectado al lanzar el script puede quedar inservible: pedir uno nuevo
            fresco = ns["bmd"].scriptapp("Resolve") if ns.get("bmd") else None
            if fresco is not None and callable(getattr(fresco, "GetVersionString", None)):
                ns["resolve"] = fresco
        except Exception:
            pass
        if req.get("token") != token:
            resp = {"ok": False, "err": "token incorrecto"}
        elif req.get("cmd") == "ping":
            r = ns["resolve"]
            resp = {"ok": True, "result": "%s %s" % (r.GetProductName(), r.GetVersionString())}
        elif req.get("cmd") == "stop":
            resp = {"ok": True, "result": "parado"}
            ns["_parar"] = True
        else:
            resp = _ejecutar(req.get("code", ""), ns)
        conn.sendall((json.dumps(resp) + "\n").encode())


def servir():
    with open(os.path.join(BASE, ".token")) as fh:
        token = fh.read().strip()
    r = _resolve()
    ns = {"resolve": r, "fusion": globals().get("fusion") or r.Fusion(), "bmd": globals().get("bmd")}
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(4)
    _log("escuchando en %s:%s" % (HOST, PORT))
    while not ns.get("_parar"):
        conn, _ = srv.accept()
        try:
            _atender(conn, token, ns)
        except Exception:
            _log(traceback.format_exc())
    srv.close()


print("Editor autónomo: puente escuchando en %s:%s" % (HOST, PORT))
try:
    servir()
except Exception:
    _log(traceback.format_exc())
