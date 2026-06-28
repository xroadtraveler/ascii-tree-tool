# [10000] Beacon: filter selection panel (Phase 1 default exclusions)

"""Filter selection panel.

Provides three checkboxes for the Phase 1 default exclusion targets:
.git/, __pycache__/, and .venv/. All are checked by default; the user may
uncheck any to include the corresponding entries in the generated tree.

The panel composes the active exclusions via combine_filters and returns the
result from get_filter(). If all checkboxes are unchecked, get_filter()
returns None, which the walker treats as 'no filter'.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from ascii_tree_tool.backend.filters import (
    FilterFn,
    combine_filters,
    exclude_git,
    exclude_pycache,
    exclude_venv,
)


# [100] Subsystem: filter selection panel widget

class FilterPanel(QWidget):
    """Panel for Phase 1 default exclusion selection.

    The panel exposes a single public method, get_filter(), which composes
    the currently-checked exclusions into a single FilterFn suitable for
    passing to walk_tree(filter_fn=...).
    """

    # [010] initialize the panel
    # [SCOPE] constructs UI elements (checkboxes inside a labeled group box); no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, reading external state to set initial checkbox values

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construct the panel with three default-checked exclusion checkboxes."""

        super().__init__(parent)

        # [001] create the three checkboxes, each default-checked
        self._cb_git = QCheckBox(".git/")
        self._cb_git.setChecked(True)
        self._cb_git.setToolTip(
            "Exclude the Git metadata directory.\n"
            "Uncheck to include .git/ in the tree (e.g., for auditing repo internals)."
        )

        self._cb_pycache = QCheckBox("__pycache__/")
        self._cb_pycache.setChecked(True)
        self._cb_pycache.setToolTip(
            "Exclude Python bytecode cache directories.\n"
            "Uncheck to include __pycache__/ in the tree."
        )

        self._cb_venv = QCheckBox(".venv/")
        self._cb_venv.setChecked(True)
        self._cb_venv.setToolTip(
            "Exclude the local Python virtual environment directory.\n"
            "Uncheck to include .venv/ in the tree."
        )
        # [-----END [001]-----]

        # [002] arrange checkboxes horizontally inside a group box
        checkbox_row = QHBoxLayout()
        checkbox_row.addWidget(self._cb_git)
        checkbox_row.addWidget(self._cb_pycache)
        checkbox_row.addWidget(self._cb_venv)
        checkbox_row.addStretch(1)
        # [-----END [002]-----]

        # [003] wrap the row in a labeled group box
        group = QGroupBox("Exclude from tree")
        group.setLayout(checkbox_row)
        # [-----END [003]-----]

        # [004] mount the group box as the panel's only child
        layout = QVBoxLayout(self)
        layout.addWidget(group)
        layout.setContentsMargins(0, 0, 0, 0)
        # [-----END [004]-----]

    # [-----END [010]-----]


    # [020] return the composed active filter or None if no boxes checked
    # [SCOPE] reads checkbox state and returns a composed FilterFn matching the active exclusions, or 
    #         None if no exclusions are active; no filesystem access
    # [OUT-OF-SCOPE] filesystem reads or writes, modifying checkbox state, raising on invalid state

    def get_filter(self) -> FilterFn | None:
        """Return the composed filter for the currently-checked exclusions.

        Returns:
            A FilterFn composing the active exclusion predicates with logical
            AND, suitable for passing to walk_tree(filter_fn=...). Returns None
            if no checkboxes are checked, which the walker interprets as
            'no filter' (include everything).
        """

        # [001] collect active predicates based on checkbox state
        active: list[FilterFn] = []
        if self._cb_git.isChecked():
            active.append(exclude_git)
        if self._cb_pycache.isChecked():
            active.append(exclude_pycache)
        if self._cb_venv.isChecked():
            active.append(exclude_venv)
        # [-----END [001]-----]

        # [002] return composed filter or None for empty active list
        if not active:
            return None
        return combine_filters(*active)
        # [-----END [002]-----]

    # [-----END [020]-----]

# [-----END [100]-----]