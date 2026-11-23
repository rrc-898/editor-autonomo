#!/usr/bin/env python3
"""Cliente del puente del Editor autónomo (habla con la sesión VIVA de DaVinci Resolve).

    cr.py ping                 ¿está el puente? versión de Resolve
    cr.py eval "expresión"     (resolve, fusion y bmd ya definidos)
    cr.py exec script.py       ejecuta un script dentro de Resolve (o «-» para leer de stdin)
    cr.py stop                 cierra el puente (vuelve a lanzarlo desde el menú de Resolve)

El puente se lanza en Resolve: Área de trabajo › Secuencias de comandos › editor_autonomo_puente
(Workspace › Scripts). Si EA_CONFIG apunta a otra configuración, se pasa también al script.
"""
import json
import os
import socket
import sys

CONFIG = os.environ.get("EA_CONFIG") or os.path.expanduser("~/.config/editor-autonomo/config.json")
BASE = os.path.dirname(CONFIG)
try:
    PORT = int(json.load(open(CONFIG, encoding="utf-8")).get("puerto", 51708))
except Exception:
    PORT = 51708
HOST = "127.0.0.1"


def send(payload, timeout=1800):
    with open(os.path.join(BASE, ".token")) as fh:
        payload["token"] = fh.read().strip()
    try:
        with socket.create_connection((HOST, PORT), timeout=10) as s:
            s.settimeout(timeout)
            s.sendall((json.dumps(payload) + "\n").encode())
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
    except ConnectionRefusedError:
        sys.exit("Nadie escucha en %s:%s. En Resolve: Área de trabajo › Secuencias de comandos › editor_autonomo_puente."
                 % (HOST, PORT))
    if not buf:
        sys.exit("Resolve cerró la conexión sin responder.")
    return json.loads(buf.decode())


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd in ("ping", "stop"):
        resp = send({"cmd": cmd})
    elif cmd == "eval":
        resp = send({"code": sys.argv[2]})
    elif cmd == "exec":
        src = sys.stdin.read() if sys.argv[2] == "-" else open(sys.argv[2], encoding="utf-8").read()
        pre = "import os as _os\n_os.environ['EA_CONFIG'] = %r\n" % CONFIG
        resp = send({"code": pre + src})
    else:
        sys.exit(__doc__)
    if resp.get("out"):
        sys.stdout.write(resp["out"])
    if resp.get("result") is not None:
        print(resp["result"])
    if not resp.get("ok"):
        sys.stderr.write(resp.get("err", "error") + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
