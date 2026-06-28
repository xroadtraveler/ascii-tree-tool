# [10000] Beacon: main window assembling all Phase 1 frontend panels

"""Main application window.

Top-level QMainWindow that assembles the four Phase 1 frontend panels
(PathPanel, FilterPanel, OutputPanel, Visualizer) and the Run button, wires
their signals to backend operations, and manages cached output content for
the three save formats.

On Run, the window walks the target directory through the configured filter,
formats the result through all three formatters, caches the formatted output
strings, and displays the ASCII content in the visualizer. The save buttons
then write the cached content to timestamped files in the configured output
location.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ascii_tree_tool.backend.formatters.ascii import format_ascii
from ascii_tree_tool.backend.formatters.csv_fmt import format_csv
from ascii_tree_tool.backend.formatters.mermaid import format_mermaid
from ascii_tree_tool.backend.tree import ASCIITreeToolError, walk_tree
from ascii_tree_tool.frontend.filter_panel import FilterPanel
from ascii_tree_tool.frontend.output_panel import OutputPanel
from ascii_tree_tool.frontend.path_panel import PathPanel
from ascii_tree_tool.frontend.visualizer import Visualizer

logger = logging.getLogger(__name__)


# [100] Subsystem: main window class

class MainWindow(QMainWindow):
    """Top-level application window.

    Owns the four panels, the Run button, and the cached output content.
    Wires user actions to backend operations and routes results to the
    visualizer and the status bar.
    """

    # [010] initialize the window and assemble all child widgets
    # [SCOPE] constructs the window, instantiates the four panels and the Run button, builds 
    #         the layout, wires signals, and initializes cached output state to empty. No 
    #         filesystem access.
    # [OUT-OF-SCOPE] filesystem reads or writes, walking trees, generating output content 
    #                during construction

    def __init__(self) -> None:
        """Construct the main window with all child widgets and wiring."""

        super().__init__()

        # [001] window-level properties
        self.setWindowTitle("ASCII Tree Tool")
        self.resize(800, 600)
        # [-----END [001]-----]

        # [002] instantiate child widgets
        self._path_panel = PathPanel()
        self._filter_panel = FilterPanel()
        self._output_panel = OutputPanel()
        self._visualizer = Visualizer()
        self._run_button = QPushButton("Run")
        self._run_button.setToolTip(
            "Scan the target directory and display the tree in the visualizer.\n"
            "Save buttons become available after a successful scan."
        )
        run_font = self._run_button.font()
        run_font.setWeight(QFont.Weight.Bold)
        self._run_button.setFont(run_font)
        # [-----END [002]-----]

        # [003] build layout: PathPanel, [FilterPanel + Run row], Visualizer, OutputPanel
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self._path_panel)

        filter_run_row = QHBoxLayout()
        filter_run_row.addWidget(self._filter_panel, stretch=1)
        filter_run_row.addWidget(self._run_button)
        layout.addLayout(filter_run_row)

        layout.addWidget(self._visualizer, stretch=1)
        layout.addWidget(self._output_panel)

        self.setCentralWidget(central)
        # [-----END [003]-----]

        # [004] wire signals
        self._run_button.clicked.connect(self._on_run_clicked)
        self._output_panel.save_ascii_requested.connect(self._on_save_ascii)
        self._output_panel.save_csv_requested.connect(self._on_save_csv)
        self._output_panel.save_mermaid_requested.connect(self._on_save_mermaid)
        # [-----END [004]-----]

        # [005] initialize cached output state to empty
        self._cached_ascii: str | None = None
        self._cached_csv: str | None = None
        self._cached_mermaid: str | None = None
        self._cached_timestamp: str | None = None
        # [-----END [005]-----]

        # [006] initial status message
        self.statusBar().showMessage("Ready. Select a target directory and click Run.")
        # [-----END [006]-----]

    # [-----END [010]-----]


    # [020] set the target path programmatically (for --target CLI arg)
    # [SCOPE] delegates to PathPanel.set_target_path; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, validating the path, triggering a scan

    def set_target_path(self, path: Path | str) -> None:
        """Programmatically set the Target Directory field.

        Used by the __main__ CLI entry point when --target is supplied.

        Args:
            path: The path to set. Delegated unchanged to PathPanel.
        """

        # [001] delegate to PathPanel
        self._path_panel.set_target_path(path)
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] handle the Run button click
    # [SCOPE] reads the target directory via walk_tree, runs all three formatters, caches 
    #         their output, displays the ASCII content in the visualizer, and enables the 
    #         save buttons on success. Logs warnings or exceptions on failure.
    # [OUT-OF-SCOPE] writes to the filesystem, modifying the configured filter or output location

    def _on_run_clicked(self) -> None:
        """Internal: scan the target, format all three outputs, and display."""

        # [001] validate target path is set
        target = self._path_panel.get_target_path()
        if target is None:
            self._set_status("Target directory not set.")
            return
        # [-----END [001]-----]

        # [002] reset UI to "in progress" state and let it repaint
        self._output_panel.set_enabled(False)
        self._visualizer.set_content("")
        self._set_status(f"Scanning {target}...")
        QApplication.processEvents()
        # [-----END [002]-----]

        # [003] walk the tree, catching project errors as user-facing messages
        try:
            filter_fn = self._filter_panel.get_filter()
            root = walk_tree(target, filter_fn=filter_fn)
        except ASCIITreeToolError as e:
            logger.warning("Scan failed for %s: %s", target, e)
            self._set_status(f"Scan failed: {e}")
            return
        except Exception as e:
            logger.exception("Unexpected error during scan of %s", target)
            self._set_status(f"Unexpected error: {e}")
            return
        # [-----END [003]-----]

        # [004] capture run timestamp before formatting so filenames match header times to the second
        self._cached_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        # [-----END [004]-----]

        # [005] format all three outputs and cache them
        try:
            self._cached_ascii = format_ascii(root)
            self._cached_csv = format_csv(root)
            self._cached_mermaid = format_mermaid(root)
        except Exception as e:
            logger.exception("Format failed after scan of %s", target)
            self._set_status(f"Format failed: {e}")
            self._clear_cache()
            return
        # [-----END [005]-----]

        # [006] display ASCII content and enable saves
        self._visualizer.set_content(self._cached_ascii)
        self._output_panel.set_enabled(True)
        line_count = len(self._cached_ascii.splitlines())
        self._set_status(f"Scan complete. {line_count} lines generated.")
        logger.info("Scan complete for %s (%d lines)", target, line_count)
        # [-----END [006]-----]

    # [-----END [030]-----]


    # [040] handle Save ASCII button click
    # [SCOPE] writes the cached ASCII content to a timestamped .txt file in the configured 
    #         output location via the shared save helper
    # [OUT-OF-SCOPE] re-walking the tree, re-formatting, modifying the cached content

    def _on_save_ascii(self) -> None:
        """Internal: save the cached ASCII content to a .txt file."""

        # [001] delegate to the shared save helper
        self._save_to_file(self._cached_ascii, "txt")
        # [-----END [001]-----]

    # [-----END [040]-----]


    # [050] handle Save CSV button click
    # [SCOPE] writes the cached CSV content to a timestamped .csv file in the configured 
    #         output location via the shared save helper
    # [OUT-OF-SCOPE] re-walking the tree, re-formatting, modifying the cached content

    def _on_save_csv(self) -> None:
        """Internal: save the cached CSV content to a .csv file."""

        # [001] delegate to the shared save helper
        self._save_to_file(self._cached_csv, "csv")
        # [-----END [001]-----]

    # [-----END [050]-----]


    # [060] handle Save Mermaid button click
    # [SCOPE] writes the cached Mermaid content to a timestamped .mermaid file in the configured 
    #         output location via the shared save helper
    # [OUT-OF-SCOPE] re-walking the tree, re-formatting, modifying the cached content

    def _on_save_mermaid(self) -> None:
        """Internal: save the cached Mermaid content to a .mermaid file."""

        # [001] delegate to the shared save helper
        self._save_to_file(self._cached_mermaid, "mermaid")
        # [-----END [001]-----]

    # [-----END [060]-----]


    # [070] write content to a timestamped file in the output location
    # [SCOPE] validates the output location, composes a timestamped filename, writes the given 
    #         content as UTF-8, and reports success or failure via the status bar
    # [OUT-OF-SCOPE] re-formatting content, modifying the cached content or panels, prompting 
    #                the user for an alternative path

    def _save_to_file(self, content: str | None, ext: str) -> None:
        """Internal: shared save logic for all three formats.

        Args:
            content: The cached content to write. None if Run has not been
                successful yet; in that case shows an error and returns.
            ext: File extension without leading dot (e.g., 'txt', 'csv').
        """

        # [001] guard against missing content
        if content is None or self._cached_timestamp is None:
            self._set_status("Nothing to save. Click Run first.")
            return
        # [-----END [001]-----]

        # [002] validate the output location
        output_dir = self._path_panel.get_output_path()
        if output_dir is None:
            self._set_status("Output location not set.")
            return
        if not output_dir.exists():
            self._set_status(f"Output location does not exist: {output_dir}")
            return
        if not output_dir.is_dir():
            self._set_status(f"Output location is not a directory: {output_dir}")
            return
        # [-----END [002]-----]

        # [003] compose the timestamped filename and write
        filename = f"ascii_tree_{self._cached_timestamp}.{ext}"
        filepath = output_dir / filename
        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            logger.warning("Save failed for %s: %s", filepath, e)
            self._set_status(f"Save failed: {e}")
            return
        # [-----END [003]-----]

        # [004] report success
        self._set_status(f"Saved: {filepath}")
        logger.info("Saved: %s", filepath)
        # [-----END [004]-----]

    # [-----END [070]-----]


    # [080] clear the cached output state
    # [SCOPE] resets cached output fields to None; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, modifying the visualizer or panels

    def _clear_cache(self) -> None:
        """Internal: clear cached output content and timestamp."""

        # [001] reset all cache fields
        self._cached_ascii = None
        self._cached_csv = None
        self._cached_mermaid = None
        self._cached_timestamp = None
        # [-----END [001]-----]

    # [-----END [080]-----]


    # [090] update the status bar message
    # [SCOPE] writes the given message to the window's status bar; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, logging, modifying any panel state

    def _set_status(self, message: str) -> None:
        """Internal: update the status bar with the given message."""

        # [001] delegate to QMainWindow's status bar
        self.statusBar().showMessage(message)
        # [-----END [001]-----]

    # [-----END [090]-----]

# [-----END [100]-----]