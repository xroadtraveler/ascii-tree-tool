# [10000] Beacon: CLI entry point and launch sequence

"""CLI entry point.

Launches the ASCII Tree Tool GUI. Supports an optional --target argument
that pre-populates the Target Directory field at startup, intended for use
by Phase 2 shell context-menu integrations and for general convenience.

Two equivalent launch paths use this module:
    1. `ascii-tree-tool` (via the gui-scripts entry point in pyproject.toml)
    2. `python -m ascii_tree_tool` (via the if __name__ == '__main__' block)

Both call main() with identical behavior.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from ascii_tree_tool import __version__
from ascii_tree_tool.frontend.main_window import MainWindow


# [100] Subsystem: CLI argument parsing

# [010] build the argparse parser for the CLI
# [SCOPE] constructs and returns an argparse.ArgumentParser configured with the --target 
#         and --version arguments. Pure factory; no I/O.
# [OUT-OF-SCOPE] parsing arguments, performing filesystem reads, launching the GUI

def _build_arg_parser() -> argparse.ArgumentParser:
    """Return the configured argparse.ArgumentParser for the CLI.

    Returns:
        An ArgumentParser with --target (optional path) and the standard
        --version flag.
    """

    # [001] construct parser with description
    parser = argparse.ArgumentParser(
        prog="ascii-tree-tool",
        description="Cross-platform GUI for generating ASCII tree representations of folder structures.",
    )
    # [-----END [001]-----]

    # [002] add --target argument
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        metavar="PATH",
        help="Pre-populate the Target Directory field with PATH at startup.",
    )
    # [-----END [002]-----]

    # [003] add --version argument
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    # [-----END [003]-----]

    return parser

# [-----END [010]-----]

# [-----END [100]-----]


# [20000] Beacon: Execution entry

# [010] launch the GUI application
# [SCOPE] parses CLI arguments, configures logging, creates the QApplication, sets the
#         application-wide window icon, instantiates and shows MainWindow, applies the
#         --target argument if given, and runs the Qt event loop until window close.
#         Reads sys.argv and the bundled icon file. May write to stderr via logging.
# [OUT-OF-SCOPE] writes to user files, validating the --target path against the filesystem, 
#                parsing arguments beyond those defined in _build_arg_parser

def main() -> None:
    """Application entry point.

    Parses CLI arguments, configures logging, builds the GUI, and starts the
    Qt event loop. Exits with the event loop's return code.
    """

    # [001] parse CLI arguments
    parser = _build_arg_parser()
    args = parser.parse_args()
    # [-----END [001]-----]

    # [002] configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    )
    # [-----END [002]-----]

    # [003] create QApplication before any widget
    app = QApplication(sys.argv)
    # [-----END [003]-----]

    # [004] set application-wide window icon
    # PyInstaller onefile mode extracts bundled data to sys._MEIPASS at runtime.
    # In dev mode (running from source), __file__ is at src/<pkg>/__main__.py,
    # so repo root is three parents up. Same path shape both ways: <base>/assets/.
    if hasattr(sys, "_MEIPASS"):
        _icon_base = Path(sys._MEIPASS)
    else:
        _icon_base = Path(__file__).resolve().parent.parent.parent
    app.setWindowIcon(QIcon(str(_icon_base / "assets" / "ASCII_Tree_Icon.ico")))
    # [-----END [004]-----]

    # [005] instantiate and configure the main window
    window = MainWindow()
    if args.target:
        window.set_target_path(args.target)
    # [-----END [005]-----]

    # [006] show and run
    window.show()
    sys.exit(app.exec())
    # [-----END [006]-----]

# [-----END [010]-----]


# [020] enforce script entry

if __name__ == "__main__":
    main()
# [-----END [020]-----]