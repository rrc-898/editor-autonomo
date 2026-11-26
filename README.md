# Editor autónomo

**Connect Claude Code to DaVinci Resolve, including the free version, for autonomous video editing.**
A bridge running inside Resolve lets the agent assemble, cut, title, colour-grade and export, with a
packaged skill, a cross-platform installer and read-only footage download from Google Drive, OneDrive and
SharePoint through rclone.

![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-free%20%26%20Studio-233A51)
![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-D97757)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

Conecta **Claude Code** con **DaVinci Resolve** para que Claude pueda editar por ti: montar, cortar, poner textos, etalonar,
revisar y exportar. Por ejemplo, un documental o una tanda de reels. Funciona también con la **versión gratuita** de Resolve y
puede bajar el material de **Google Drive, OneDrive o SharePoint** con rclone.

```
Claude Code ──cr.py──▶ 127.0.0.1:51708 ──▶ puente dentro de Resolve ──▶ API de scripting de Resolve
     ▲                                                                         │
     └──────────── fotogramas y renders para comprobar lo que ha hecho ◀───────┘
```

## Por qué hace falta un puente
La versión gratuita de Resolve no deja que un programa externo use su API (`scriptapp("Resolve")` devuelve `None`), pero sí
ejecuta los scripts de su propio menú. El puente es uno de esos scripts: se lanza desde **Área de trabajo › Secuencias de
comandos** y abre un servidor local, protegido con un token, que ejecuta los scripts de Python que le manda Claude con
`resolve`, `fusion` y `bmd` ya definidos. En la versión Studio funciona igual.

## Requisitos
- DaVinci Resolve 18 o más nuevo (probado con la 21 gratuita en Linux).
- Python 3.6+ y [Claude Code](https://claude.com/claude-code).
- Opcional: [rclone](https://rclone.org/install/) para bajar material de la nube y `ffmpeg` (en Linux, Resolve gratuito no lee H.264 ni AAC).

## Instalación
```bash
git clone https://github.com/rrc-898/editor-autonomo.git
cd editor-autonomo
python3 install.py          # en Windows: python install.py
```
El instalador:
1. crea `~/.config/editor-autonomo/` con el puerto y un token aleatorio;
2. copia el puente al menú de scripts de Resolve (`Fusion/Scripts/Utility` de tu sistema);
3. instala la skill `davinci-resolve` en `~/.claude/skills/`, con las rutas de tu equipo;
4. avisa si falta rclone.

Para quitarlo todo: `python3 install.py --desinstalar`.

## Uso
1. Abre Resolve con tu proyecto.
2. **Área de trabajo › Secuencias de comandos › editor_autonomo_puente** (Workspace › Scripts). Se queda escuchando.
   Si no aparece en el menú, cierra y vuelve a abrir Resolve (lee la carpeta de scripts al arrancar).
3. Comprueba la conexión: `python3 puente/cr.py ping` → `DaVinci Resolve 21.x`.
4. Abre Claude Code y pídele lo que quieras, por ejemplo:
   - «Baja la carpeta *Rodaje* de mi Drive y haz un primer montaje de 3 minutos con las entrevistas».
   - «Pon subtítulos a la entrevista de la línea de tiempo *Corte 2* y enséñame cómo quedan».
   - «Etalona los planos de exterior para que casen y exporta un ProRes».

Claude lee la documentación de la API de **tu** instalación de Resolve, trabaja sobre duplicados de tus líneas de tiempo y te
enseña fotogramas para que revises.

### Órdenes a mano
```bash
python3 puente/cr.py ping                       # ¿hay conexión?
python3 puente/cr.py eval "resolve.GetCurrentPage()"
python3 puente/cr.py exec ejemplos/estado.py    # proyecto, líneas de tiempo, pistas, clips, bins
python3 puente/cr.py exec ejemplos/fotograma.py # fotograma del cabezal a PNG
python3 puente/cr.py stop                       # cierra el puente
```

### Material en la nube
```bash
rclone config                                              # una vez: crea el remoto (Drive, OneDrive/SharePoint…)
python3 herramientas/nube.py remotos
python3 herramientas/nube.py ver midrive:Rodaje            # qué hay y cuánto ocupa
python3 herramientas/nube.py bajar midrive:Rodaje ~/Rodaje # comprueba el espacio, baja y verifica
python3 herramientas/nube.py ver midrive: --carpeta-id ID  # carpeta compartida por enlace (…/folders/ID)
```
`nube.py` solo lee: nunca sube, borra ni sincroniza.

## Contenido
| Ruta | Qué es |
|---|---|
| `puente/editor_autonomo_puente.py` | El script que corre dentro de Resolve |
| `puente/cr.py` | Cliente: `ping`, `eval`, `exec`, `stop` |
| `puente/xclick.py` | Opcional, Linux/X11: clics y teclas en la interfaz de Resolve |
| `herramientas/nube.py` | Descargas con rclone (Drive, OneDrive, SharePoint…) |
| `skill/davinci-resolve/SKILL.md` | Lo que Claude necesita saber: conexión, recetas comprobadas y trampas |
| `ejemplos/` | Scripts de prueba |
| `install.py` | Instalador para Linux, macOS y Windows |

## Seguridad
- El puente solo escucha en `127.0.0.1` (tu propio equipo) y exige el token de `~/.config/editor-autonomo/.token`.
- Cualquiera que tenga ese token puede ejecutar código dentro de Resolve con tus permisos: no lo compartas.
- Cierra el puente con `cr.py stop` o cerrando Resolve cuando no lo uses.

## Probado
- Linux (Fedora), DaVinci Resolve 21.0.4 gratuito: conexión, montaje, Text+, color por CDL y render.
- macOS y Windows: rutas del instalador según la documentación de Blackmagic, sin probar todavía. Si algo falla, abre un issue.

## Licencia
MIT
