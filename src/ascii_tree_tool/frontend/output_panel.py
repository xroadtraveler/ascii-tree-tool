# [10000] Beacon: output save panel (three format buttons)

"""Output save panel.

Provides three buttons for saving the current tree output in the three Phase 1
formats: ASCII tree (.txt), CSV, and Mermaid. Each button emits a distinct
signal when clicked; the main window connects these signals to handlers that
read the visualizer content and write the appropriate file.

The ASCII button is the default action (Enter key triggers it in dialog
contexts, and its label is bold to provide a visual hint).

All three buttons are disabled at construction and enabled by the main window
via set_enabled() once there is generated content to save.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)


# [100] Subsystem: output save panel widget

class OutputPanel(QWidget):
    """Panel with three save buttons, one per Phase 1 output format.

    Signals:
        save_ascii_requested: Emitted when the ASCII (.txt) save button is clicked.
        save_csv_requested: Emitted when the CSV save button is clicked.
        save_mermaid_requested: Emitted when the Mermaid save button is clicked.
    """

    save_ascii_requested = pyqtSignal()
    save_csv_requested = pyqtSignal()
    save_mermaid_requested = pyqtSignal()

    # [010] initialize the panel
    # [SCOPE] constructs three save buttons and wires their clicked signals to the panel's emit signals; 
    #         no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, opening file dialogs, emitting save signals 
    #         during construction

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construct the panel with three disabled save buttons."""

        super().__init__(parent)

        # [001] build the ASCII button as the default action with bold label
        self._btn_ascii = QPushButton("Save ASCII (.txt)")
        self._btn_ascii.setDefault(True)
        bold_font = self._btn_ascii.font()
        bold_font.setWeight(QFont.Weight.Bold)
        self._btn_ascii.setFont(bold_font)
        self._btn_ascii.setToolTip(
            "Save the visible tree as an ASCII .txt file.\n"
            "This is the default format (Enter key triggers it in dialog contexts)."
        )
        self._btn_ascii.clicked.connect(self.save_ascii_requested.emit)
        # [-----END [001]-----]

        # [002] build the CSV button
        self._btn_csv = QPushButton("Save CSV")
        self._btn_csv.setToolTip(
            "Save the tree as a CSV file with path, type, and depth columns.\n"
            "Useful for spreadsheet inspection and programmatic consumption."
        )
        self._btn_csv.clicked.connect(self.save_csv_requested.emit)
        # [-----END [002]-----]

        # [003] build the Mermaid button
        self._btn_mermaid = QPushButton("Save Mermaid")
        self._btn_mermaid.setToolTip(
            "Save the tree as a Mermaid flowchart diagram.\n"
            "Embed in Markdown that supports Mermaid rendering (GitHub, GitLab, etc.)."
        )
        self._btn_mermaid.clicked.connect(self.save_mermaid_requested.emit)
        # [-----END [003]-----]

        # [004] disable all three until enabled externally
        self._btn_ascii.setEnabled(False)
        self._btn_csv.setEnabled(False)
        self._btn_mermaid.setEnabled(False)
        # [-----END [004]-----]

        # [005] arrange buttons horizontally
        layout = QHBoxLayout(self)
        layout.addWidget(self._btn_ascii)
        layout.addWidget(self._btn_csv)
        layout.addWidget(self._btn_mermaid)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        # [-----END [005]-----]

    # [-----END [010]-----]


    # [020] enable or disable all three save buttons together
    # [SCOPE] sets the enabled state of all three save buttons to the given value; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, partial enable/disable (single-button toggling)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all three save buttons together.

        Used by the main window to gate saving on whether the visualizer has
        content. Called with True after a successful Run, with False before
        any Run has occurred or after the target directory is cleared.

        Args:
            enabled: True to enable all three buttons, False to disable.
        """

        # [001] apply uniformly to all three buttons
        self._btn_ascii.setEnabled(enabled)
        self._btn_csv.setEnabled(enabled)
        self._btn_mermaid.setEnabled(enabled)
        # [-----END [001]-----]

    # [-----END [020]-----]

# [-----END [100]-----]