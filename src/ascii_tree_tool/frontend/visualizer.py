# [10000] Beacon: tree visualizer (Phase 1 plain-text display)

"""Tree visualizer widget.

Displays formatted tree output (typically the ASCII tree from
backend.formatters.ascii.format_ascii) as read-only monospace text.

Phase 1 implementation uses QPlainTextEdit. Phase 2 will swap this entire
module for a QTreeView-based interactive widget supporting expand/collapse,
right-click 'open file/folder', and the annotation column. The public API
(set_content, get_content) will be preserved across the swap, so callers in
main_window.py don't need to change.
"""

from __future__ import annotations

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QPlainTextEdit, QWidget


# [100] Subsystem: tree visualizer widget

class Visualizer(QPlainTextEdit):
    """Read-only monospace text widget for displaying formatted tree output.

    The widget preserves snapshot semantics: get_content() returns exactly the
    text last passed to set_content(), regardless of when get_content() is
    called. This means Save actions save what the user is looking at, not a
    re-generated tree that may differ.
    """

    # [010] initialize the visualizer
    # [SCOPE] configures the widget as a read-only monospace plain-text editor with appropriate 
    #         display settings; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, syntax highlighting, populating content 
    #         during construction

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construct the visualizer as an empty read-only monospace widget."""

        super().__init__(parent)

        # [001] make the widget read-only while preserving selection for copy
        self.setReadOnly(True)
        # [-----END [001]-----]

        # [002] apply the platform's preferred monospace font for tree-art alignment
        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.setFont(fixed_font)
        # [-----END [002]-----]

        # [003] disable word wrap; long paths scroll horizontally
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        # [-----END [003]-----]

        # [004] set tab stops to 4 spaces width (belt-and-suspenders for any future tab content)
        font_metrics = self.fontMetrics()
        tab_width_pixels = font_metrics.horizontalAdvance(" " * 4)
        self.setTabStopDistance(tab_width_pixels)
        # [-----END [004]-----]

        # [005] placeholder text shown when the widget is empty
        self.setPlaceholderText("Click Run to generate the tree...")
        # [-----END [005]-----]

    # [-----END [010]-----]


    # [020] set the visualizer's content, replacing any existing text
    # [SCOPE] replaces the widget's text content with the given string and scrolls to the top; 
    #         no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, parsing or modifying the content, emitting 
    #                change signals

    def set_content(self, text: str) -> None:
        """Replace the visualizer's content with the given text.

        Scrolls back to the top after setting so the user sees the beginning
        of the new tree, not wherever the previous tree was scrolled to.

        Args:
            text: The formatted tree text to display. Typically the output of
                a backend formatter (format_ascii, etc.).
        """

        # [001] replace content and scroll to top
        self.setPlainText(text)
        self.verticalScrollBar().setValue(0)
        self.horizontalScrollBar().setValue(0)
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] return the visualizer's current content as a string
    # [SCOPE] returns the widget's current text content unchanged; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, modifying the content, re-running the formatter

    def get_content(self) -> str:
        """Return the visualizer's current content as a string.

        Returns exactly the text last passed to set_content(), preserving
        snapshot semantics for save actions.

        Returns:
            The current widget content as a string. Empty string if no content
            has been set.
        """

        # [001] read and return current content
        return self.toPlainText()
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [100]-----]