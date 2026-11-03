# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


root = Path(SPECPATH)
root_files = [
    "index.html",
    "client-fixes.js",
    "desktop-client.js",
    "manifest.json",
    "icon-192.svg",
    "icon-512.svg",
    "approved.mp3",
    "rejected.mp3",
    "click.mp3",
    "notify.mp3",
    "dossier_447_gn_player.html",
    "launcher.html",
    "Icona DKM.png",
    "(NEW) Dossier operazione mareggiata.pdf",
    "(NEW) FBI Dossier Interrogatori Completi.txt",
    "(NEW) soluzione Caso 447GN Mareggiata.txt",
    "(NEW) EV-04.png",
    "(NEW) EV-05.png",
    "(NEW) planimetria della Sala Blu.png",
]
datas = [(str(root / name), ".") for name in root_files]
datas.extend(
    (str(path), str(path.relative_to(root).parent))
    for path in (root / "assets").rglob("*")
    if path.is_file()
)
hiddenimports = {
    "darwin": ["webview.platforms.cocoa"],
    "win32": ["webview.platforms.winforms"],
    "linux": ["webview.platforms.gtk"],
}.get(sys.platform, [])

a = Analysis(
    [str(root / "launcher.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OperationMareggiata",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(root / "Icona DKM.ico") if sys.platform == "win32" else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="OperationMareggiata",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="OperationMareggiata.app",
        icon=str(root / "Icona DKM.icns"),
        bundle_identifier="com.operationmareggiata.desktop",
    )
