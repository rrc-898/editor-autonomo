#!/usr/bin/env python3
"""Instala el puente Claude Code ↔ DaVinci Resolve (Linux, macOS y Windows).

    python3 install.py              instala (o actualiza)
    python3 install.py --puerto N   usa otro puerto local (51708 por defecto)
    python3 install.py --desinstalar

Qué hace:
  1. ~/.config/editor-autonomo/  config.json (puerto) y .token (secreto aleatorio que solo conocen el puente y cr.py)
  2. Copia el puente al menú de scripts de Resolve (carpeta Fusion/Scripts/Utility de tu sistema)
  3. Copia la skill «davinci-resolve» a ~/.claude/skills/ para que Claude Code sepa usarlo
  4. Avisa si falta rclone (opcional, para bajar material de la nube)
No toca tus proyectos de Resolve ni instala nada con permisos de administrador.
"""
import argparse
import json
import os
import platform
import secrets
import shutil
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.expanduser("~/.config/editor-autonomo")
SKILL_DST = os.path.expanduser("~/.claude/skills/davinci-resolve")
NOMBRE = "editor_autonomo_puente.py"


def carpeta_scripts():
    s = platform.system()
    if s == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility")
    if s == "Windows":
        return os.path.join(os.environ["APPDATA"], "Blackmagic Design", "DaVinci Resolve", "Support", "Fusion", "Scripts", "Utility")
    return os.path.expanduser("~/.local/share/DaVinciResolve/Fusion/Scripts/Utility")


def documentacion_api():
    s = platform.system()
    if s == "Darwin":
        return "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/README.txt"
    if s == "Windows":
        return os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Blackmagic Design", "DaVinci Resolve",
                            "Support", "Developer", "Scripting", "README.txt")
    return "/opt/resolve/Developer/Scripting/README.txt"


def instalar(puerto):
    os.makedirs(CONF, exist_ok=True)
    cfg_path = os.path.join(CONF, "config.json")
    cfg = json.load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}
    cfg["puerto"] = puerto or cfg.get("puerto", 51708)
    cfg["repo"] = REPO
    json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), indent=1)
    tok = os.path.join(CONF, ".token")
    if not os.path.exists(tok):
        with open(tok, "w") as fh:
            fh.write(secrets.token_hex(16))
        try:
            os.chmod(tok, 0o600)
        except OSError:
            pass
    dst = carpeta_scripts()
    os.makedirs(dst, exist_ok=True)
    shutil.copyfile(os.path.join(REPO, "puente", NOMBRE), os.path.join(dst, NOMBRE))
    # skill para Claude Code, con las rutas de ESTE equipo ya puestas
    if os.path.isdir(SKILL_DST):
        shutil.rmtree(SKILL_DST)
    shutil.copytree(os.path.join(REPO, "skill", "davinci-resolve"), SKILL_DST)
    py = "python" if platform.system() == "Windows" else "python3"
    md = os.path.join(SKILL_DST, "SKILL.md")
    txt = open(md, encoding="utf-8").read()
    txt = txt.replace("{{CR}}", f'{py} "{os.path.join(REPO, "puente", "cr.py")}"')
    txt = txt.replace("{{EJEMPLOS}}", os.path.join(REPO, "ejemplos"))
    txt = txt.replace("{{NUBE}}", f'{py} "{os.path.join(REPO, "herramientas", "nube.py")}"')
    txt = txt.replace("{{API_README}}", documentacion_api())
    open(md, "w", encoding="utf-8").write(txt)
    print("Instalado.")
    print(f"  configuración : {cfg_path} (puerto {cfg['puerto']})")
    print(f"  puente        : {os.path.join(dst, NOMBRE)}")
    print(f"  skill         : {SKILL_DST}")
    print()
    print("Siguiente paso: abre DaVinci Resolve con un proyecto y lanza")
    print("  Área de trabajo › Secuencias de comandos › editor_autonomo_puente   (Workspace › Scripts)")
    print(f"y comprueba la conexión:  {py} \"{os.path.join(REPO, 'puente', 'cr.py')}\" ping")
    if not shutil.which("rclone"):
        print("\nOpcional: instala rclone para bajar material de Google Drive, OneDrive o SharePoint:")
        print("  Linux: sudo -v ; curl https://rclone.org/install.sh | sudo bash   ·   macOS: brew install rclone")
        print("  Windows: winget install Rclone.Rclone   ·   después, una vez: rclone config")
    if not os.path.exists(documentacion_api()):
        print(f"\nAviso: no encuentro la documentación de la API en {documentacion_api()}.")
        print("Busca README.txt en la carpeta Developer/Scripting de tu instalación de Resolve.")


def desinstalar():
    for p in (os.path.join(carpeta_scripts(), NOMBRE), SKILL_DST, CONF):
        if os.path.isdir(p):
            shutil.rmtree(p); print("borrado", p)
        elif os.path.exists(p):
            os.remove(p); print("borrado", p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puerto", type=int)
    ap.add_argument("--desinstalar", action="store_true")
    a = ap.parse_args()
    if sys.version_info < (3, 6):
        sys.exit("Hace falta Python 3.6 o más nuevo.")
    desinstalar() if a.desinstalar else instalar(a.puerto)
