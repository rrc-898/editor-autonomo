#!/usr/bin/env python3
"""Raton y teclado sinteticos por XTEST, para conducir la interfaz de Resolve.

Resolve es un cliente Qt5/X11 corriendo bajo XWayland, asi que responde a
XTEST aunque el escritorio sea Wayland. Hyprland puede mover el cursor y
enviar teclas, pero NO expone botones de raton; esto cubre ese hueco.

No necesita root: XTEST es una extension estandar del servidor X.

Uso:
    xclick.py pos                          posicion actual del cursor
    xclick.py move X Y
    xclick.py click X Y [--button 1] [--double]
    xclick.py drag X1 Y1 X2 Y2
    xclick.py key <keysym> [--mods ctrl,alt,shift]
    xclick.py type "texto"
"""
import argparse
import sys
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

MOD_KEYS = {
    "ctrl": "Control_L", "control": "Control_L",
    "alt": "Alt_L", "shift": "Shift_L", "super": "Super_L",
}


def get_display():
    try:
        return display.Display()
    except Exception as exc:
        sys.exit("No pude abrir el display X (%s). ¿Esta DISPLAY definido?" % exc)


def _sync(d):
    d.sync()
    time.sleep(0.05)


def cmd_pos(d):
    p = d.screen().root.query_pointer()
    return {"x": p.root_x, "y": p.root_y}


def cmd_move(d, x, y):
    xtest.fake_input(d, X.MotionNotify, x=x, y=y)
    _sync(d)
    return cmd_pos(d)


def cmd_click(d, x, y, button=1, double=False):
    cmd_move(d, x, y)
    time.sleep(0.12)
    rounds = 2 if double else 1
    for i in range(rounds):
        xtest.fake_input(d, X.ButtonPress, button)
        _sync(d)
        xtest.fake_input(d, X.ButtonRelease, button)
        _sync(d)
        if double and i == 0:
            time.sleep(0.06)
    return {"clicked": [x, y], "button": button, "double": double}


def cmd_drag(d, x1, y1, x2, y2, steps=12):
    cmd_move(d, x1, y1)
    time.sleep(0.12)
    xtest.fake_input(d, X.ButtonPress, 1)
    _sync(d)
    for i in range(1, steps + 1):
        cmd_move(d, x1 + (x2 - x1) * i // steps, y1 + (y2 - y1) * i // steps)
    time.sleep(0.12)
    xtest.fake_input(d, X.ButtonRelease, 1)
    _sync(d)
    return {"dragged": [x1, y1, x2, y2]}


def _keycode(d, keysym_name):
    ks = XK.string_to_keysym(keysym_name)
    if ks == 0:
        sys.exit("Keysym desconocido: %s" % keysym_name)
    kc = d.keysym_to_keycode(ks)
    if kc == 0:
        sys.exit("Sin keycode para: %s" % keysym_name)
    return kc


def cmd_key(d, keysym_name, mods=None):
    mods = [m.strip().lower() for m in (mods or "").split(",") if m.strip()]
    mod_codes = [_keycode(d, MOD_KEYS[m]) for m in mods if m in MOD_KEYS]
    kc = _keycode(d, keysym_name)
    for mc in mod_codes:
        xtest.fake_input(d, X.KeyPress, mc)
    _sync(d)
    xtest.fake_input(d, X.KeyPress, kc)
    _sync(d)
    xtest.fake_input(d, X.KeyRelease, kc)
    _sync(d)
    for mc in reversed(mod_codes):
        xtest.fake_input(d, X.KeyRelease, mc)
    _sync(d)
    return {"key": keysym_name, "mods": mods}


def cmd_type(d, text):
    for ch in text:
        name = {" ": "space", "\n": "Return", "\t": "Tab",
                "-": "minus", "_": "underscore", ".": "period",
                "/": "slash", ":": "colon"}.get(ch, ch)
        ks = XK.string_to_keysym(name)
        if ks == 0:
            continue
        kc = d.keysym_to_keycode(ks)
        if kc == 0:
            continue
        need_shift = ch.isupper() or ch in '_:"?'
        if need_shift:
            xtest.fake_input(d, X.KeyPress, _keycode(d, "Shift_L"))
            _sync(d)
        xtest.fake_input(d, X.KeyPress, kc)
        _sync(d)
        xtest.fake_input(d, X.KeyRelease, kc)
        _sync(d)
        if need_shift:
            xtest.fake_input(d, X.KeyRelease, _keycode(d, "Shift_L"))
            _sync(d)
    return {"typed": len(text)}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("pos")

    p_move = sub.add_parser("move")
    p_move.add_argument("x", type=int)
    p_move.add_argument("y", type=int)

    p_click = sub.add_parser("click")
    p_click.add_argument("x", type=int)
    p_click.add_argument("y", type=int)
    p_click.add_argument("--button", type=int, default=1)
    p_click.add_argument("--double", action="store_true")

    p_drag = sub.add_parser("drag")
    for n in ("x1", "y1", "x2", "y2"):
        p_drag.add_argument(n, type=int)

    p_key = sub.add_parser("key")
    p_key.add_argument("keysym")
    p_key.add_argument("--mods", default="")

    p_type = sub.add_parser("type")
    p_type.add_argument("text")

    a = ap.parse_args()
    d = get_display()

    if a.cmd == "pos":
        r = cmd_pos(d)
    elif a.cmd == "move":
        r = cmd_move(d, a.x, a.y)
    elif a.cmd == "click":
        r = cmd_click(d, a.x, a.y, a.button, a.double)
    elif a.cmd == "drag":
        r = cmd_drag(d, a.x1, a.y1, a.x2, a.y2)
    elif a.cmd == "key":
        r = cmd_key(d, a.keysym, a.mods)
    elif a.cmd == "type":
        r = cmd_type(d, a.text)

    print(r)


if __name__ == "__main__":
    main()
