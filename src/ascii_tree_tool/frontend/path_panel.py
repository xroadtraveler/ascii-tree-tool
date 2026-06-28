# [10000] Beacon: path selection panel (target directory and output location)

"""Path selection panel.

Provides two labeled fields with Browse buttons: Target Directory (the folder
to scan) and Output Location (where formatter files are saved).

The output field autofills to target.parent when the user picks a target,
unless the user has manually edited the output field with a custom value.
The override is detected by comparing the current output value to the last
autofilled value; mismatch means the user has overridden and autofill defers
to them.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_OUTPUT_TOOLTIP = (
    "Where output files (.txt, .csv, .mermaid) are saved.\n\n"
    "Defaults to one level above the target folder. This works well when you "
    "keep a parent-project folder containing both the cloned repo and your "
    "local notes (e.g., 'My_Project/' containing both 'my-project/' and "
    "untracked notes/files). The tree snapshot lands next to your notes rather "
    "than inside the repo, where it won't be accidentally committed.\n\n"
    "You can override this with any folder you prefer, and/or transfer to docs/ "
    "folder if desired before committing."
)


# [100] Subsystem: path selection panel widget

class PathPanel(QWidget):
    """Panel for target and output path selection.

    Signals:
        target_changed: Emitted whenever the Target Directory field changes
            (via typing or Browse). The argument is the current field value
            as a string; consumers should convert to Path themselves if they
            need filesystem semantics.
    """

    target_changed = pyqtSignal(str)

    # [010] initialize the panel
    # [SCOPE] constructs UI elements and wires internal signal connections; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, opening dialogs, emitting target_changed 
    #                during construction

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construct the panel and wire internal connections."""

        super().__init__(parent)

        # [001] tracks the last autofilled output value; None means no autofill has happened yet
        self._last_autofilled_output: str | None = None
        # [-----END [001]-----]

        # [002] build target row
        self._target_field = QLineEdit()
        self._target_field.setPlaceholderText("Path to the folder to scan...")
        target_browse = QPushButton("Browse...")
        target_browse.clicked.connect(self._on_target_browse)
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target Directory:"))
        target_row.addWidget(self._target_field, stretch=1)
        target_row.addWidget(target_browse)
        # [-----END [002]-----]

        # [003] build output row
        self._output_field = QLineEdit()
        self._output_field.setPlaceholderText("Where output files will be saved...")
        self._output_field.setToolTip(_OUTPUT_TOOLTIP)
        output_label = QLabel("Output Location:")
        output_label.setToolTip(_OUTPUT_TOOLTIP)
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self._on_output_browse)
        output_row = QHBoxLayout()
        output_row.addWidget(output_label)
        output_row.addWidget(self._output_field, stretch=1)
        output_row.addWidget(output_browse)
        # [-----END [003]-----]

        # [004] stack rows vertically
        layout = QVBoxLayout(self)
        layout.addLayout(target_row)
        layout.addLayout(output_row)
        layout.setContentsMargins(0, 0, 0, 0)
        # [-----END [004]-----]

        # [005] wire target field changes to autofill and external signal
        self._target_field.textChanged.connect(self._on_target_text_changed)
        # [-----END [005]-----]

    # [-----END [010]-----]


    # [020] return the current target path as a Path object or None
    # [SCOPE] reads the target field value and returns it as a Path, or None if empty; no 
    #         filesystem access
    # [OUT-OF-SCOPE] validating path existence, modifying the field

    def get_target_path(self) -> Path | None:
        """Return the Target Directory field value as a Path, or None if empty.

        The returned Path is NOT validated against the filesystem; callers are
        responsible for checking existence and type via walk_tree or directly.
        """

        # [001] read and strip the field
        text = self._target_field.text().strip()
        return Path(text) if text else None
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] return the current output path as a Path object or None
    # [SCOPE] reads the output field value and returns it as a Path, or None if empty; no 
    #         filesystem access
    # [OUT-OF-SCOPE] validating path existence, modifying the field

    def get_output_path(self) -> Path | None:
        """Return the Output Location field value as a Path, or None if empty.

        The returned Path is NOT validated against the filesystem; callers are
        responsible for checking writability before saving.
        """

        # [001] read and strip the field
        text = self._output_field.text().strip()
        return Path(text) if text else None
        # [-----END [001]-----]

    # [-----END [030]-----]


    # [040] set the target path programmatically (used by __main__ for --target CLI arg)
    # [SCOPE] populates the target field with the given path string, triggering autofill; no 
    #         filesystem access
    # [OUT-OF-SCOPE] validating path existence, suppressing the target_changed signal

    def set_target_path(self, path: Path | str) -> None:
        """Programmatically set the Target Directory field.

        Triggers the normal autofill cascade as if the user had typed the path.
        Used by the __main__ CLI entry point when --target is supplied.

        Args:
            path: The path to set. Accepts both Path and str for convenience.
        """

        # [001] write to the field; textChanged signal handles the rest
        self._target_field.setText(str(path))
        # [-----END [001]-----]

    # [-----END [040]-----]


    # [050] handle target Browse button click
    # [SCOPE] opens a native folder picker dialog and writes the result to the target field. Reads 
    #         filesystem to determine valid starting directory.
    # [OUT-OF-SCOPE] writes to the filesystem, validating the chosen folder beyond Qt's built-in checks

    def _on_target_browse(self) -> None:
        """Internal: open a folder picker and populate the Target Directory field."""

        # [001] determine starting directory: current value if valid, else home
        current = self._target_field.text().strip()
        start_dir = current if current and Path(current).is_dir() else str(Path.home())
        # [-----END [001]-----]

        # [002] open the dialog
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Target Directory", start_dir
        )
        # [-----END [002]-----]

        # [003] populate field only if user did not cancel
        if chosen:
            self._target_field.setText(chosen)
        # [-----END [003]-----]

    # [-----END [050]-----]


    # [060] handle output Browse button click
    # [SCOPE] opens a native folder picker dialog and writes the result to the output field. Reads 
    #         filesystem to determine valid starting directory.
    # [OUT-OF-SCOPE] writes to the filesystem, validating the chosen folder beyond Qt's built-in checks

    def _on_output_browse(self) -> None:
        """Internal: open a folder picker and populate the Output Location field."""

        # [001] determine starting directory: current value, then target's parent, then home
        current = self._output_field.text().strip()
        if current and Path(current).is_dir():
            start_dir = current
        else:
            target = self._target_field.text().strip()
            if target and Path(target).is_dir():
                start_dir = str(Path(target).parent)
            else:
                start_dir = str(Path.home())
        # [-----END [001]-----]

        # [002] open the dialog
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Output Location", start_dir
        )
        # [-----END [002]-----]

        # [003] populate field only if user did not cancel; mark as manual override
        if chosen:
            self._output_field.setText(chosen)
            # User explicitly chose this, so disable autofill until cleared.
            self._last_autofilled_output = None
        # [-----END [003]-----]

    # [-----END [060]-----]


    # [070] react to target field text changes
    # [SCOPE] updates the output field via autofill when appropriate and emits target_changed; no 
    #         filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, overriding a user-customized output value

    def _on_target_text_changed(self, new_text: str) -> None:
        """Internal: handle Target Directory text changes.

        Autofills the output field with target.parent if the output field is
        empty OR still equals the last autofilled value (indicating no manual
        override). Emits target_changed unconditionally so other panels can
        react to typing or programmatic changes.
        """

        # [001] decide whether to autofill the output field
        current_output = self._output_field.text().strip()
        should_autofill = (
            not current_output
            or current_output == self._last_autofilled_output
        )
        # [-----END [001]-----]

        # [002] perform autofill if appropriate and target is a non-empty path
        if should_autofill and new_text.strip():
            try:
                target_path = Path(new_text.strip())
                # Path('.').parent equals Path('.'); explicitly use '..' for autofill.
                if str(target_path) == ".":
                    parent = ".."
                else:
                    parent = str(target_path.parent)
                self._output_field.setText(parent)
                self._last_autofilled_output = parent
            except (OSError, ValueError):
                # Malformed path string while user is mid-type; ignore silently.
                pass
        # [-----END [002]-----]

        # [003] emit external signal
        self.target_changed.emit(new_text)
        # [-----END [003]-----]

    # [-----END [070]-----]

# [-----END [100]-----]