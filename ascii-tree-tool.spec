# [10000] Beacon intent: Imports

import sys
from pathlib import Path


# [20000] Beacon intent: Configuration constants for PyInstaller build

# [010] Path and asset resolution
_REPO_ROOT = Path(SPECPATH)
_ASSETS_DIR = _REPO_ROOT / "assets"
_ENTRY_SCRIPT = str(_REPO_ROOT / "run_gui.py")
_APP_NAME = "ascii-tree-tool"
# [-----END [010]-----]

# [020] Per-OS icon selection
# Windows: .ico embedded into the .exe file header.
# macOS:   .icns embedded into the .app bundle. Not yet generated
#          (deferred until Mac access). Falls back to no icon.
# Linux:   PyInstaller does not embed icons into ELF binaries; desktop
#          icon integration via .desktop files is out of scope.
if sys.platform == "win32":
    _ICON_PATH = str(_ASSETS_DIR / "ASCII_Tree_Icon.ico")
elif sys.platform == "darwin":
    _ICNS = _ASSETS_DIR / "ASCII_Tree_Icon.icns"
    _ICON_PATH = str(_ICNS) if _ICNS.exists() else None
else:
    _ICON_PATH = None
# [-----END [020]-----]

# [030] Hidden imports declaration
# PyInstaller's static analysis catches most PyQt6 submodules automatically.
# PyQt6.sip is the classic exception -- loaded via C extension mechanisms
# that static analysis sometimes misses. If the built .exe launches cleanly,
# this list can be trimmed. If it fails at startup with ModuleNotFoundError
# for a PyQt6 submodule, add that module here and rebuild.
_HIDDEN_IMPORTS = [
    "PyQt6.sip",
]
# [-----END [030]-----]


# [30000] Beacon intent: PyInstaller build definition

# [010] Analysis: source tree scan and dependency collection
a = Analysis(
    [_ENTRY_SCRIPT],
    pathex=[str(_REPO_ROOT / "src")],
    binaries=[],
        datas=[
        # Icon file bundled for QApplication.setWindowIcon() at runtime.
        # Placed at 'assets/' inside the bundle to mirror the dev-mode
        # repo layout, so the same path resolution works in both modes.
        (str(_ASSETS_DIR / "ASCII_Tree_Icon.ico"), "assets"),
    ],
    hiddenimports=_HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# [-----END [010]-----]

# [020] PYZ: compress pure-Python modules into a single archive
pyz = PYZ(a.pure)
# [-----END [020]-----]

# [030] EXE: assemble the final onefile executable
# --onefile equivalent: passing a.binaries, a.datas, and a.zipfiles
#   directly into EXE (rather than a separate COLLECT step) tells
#   PyInstaller to produce a single self-extracting .exe.
# console=False: equivalent to the --windowed / --noconsole CLI flag.
#   Suppresses the Windows cmd window that would otherwise pop up
#   behind the GUI at launch. Required for a polished GUI app.
# upx=True: PyInstaller uses UPX to compress the .exe if UPX is installed;
#   silently skips otherwise. Smaller binary, but occasionally trips
#   Windows antivirus false positives. Flip to upx=False if AV becomes
#   a problem for distribution.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=_APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_ICON_PATH,
)
# [-----END [030]-----]