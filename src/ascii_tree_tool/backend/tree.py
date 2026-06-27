# [10000] Beacon: tree data model and directory walker

"""Tree data model and directory walker.

Defines TreeNode (the canonical structural representation of a directory tree)
and walk_tree (the function that builds a TreeNode from a real directory).

All output formatters in backend.formatters consume TreeNode instances.
The frontend visualizer in Phase 1 renders the ASCII formatter output as
plain text; Phase 2 will consume TreeNode directly for interactive display.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# [100] Subsystem: exceptions

class ASCIITreeToolError(Exception):
    """Base exception for all ascii-tree-tool errors.

    All exceptions raised by ascii_tree_tool inherit from this class.
    Library consumers (including Modun) can catch this base to handle
    any tool error generically.
    """


class InvalidTargetError(ASCIITreeToolError):
    """Raised when the walker is given a path that does not exist or is not a directory."""

# [-----END [100]-----]


# [200] Subsystem: tree data model

@dataclass
class TreeNode:
    """Structural representation of one filesystem entry.

    Attributes:
        path: Path to this entry (absolute or relative; preserved as given).
        name: The basename component of the path (the display name).
        is_dir: True if this entry is a real directory (not a symlink to one).
        children: Ordered list of child TreeNodes. Empty for files, for
            unreadable directories, and for symlinks.

    The structure is recursive: a directory's children are TreeNodes that may
    themselves have children. Files and symlinks are always leaves.

    The path attribute is the stable key for the Phase 2 annotation column.
    """

    path: Path
    name: str
    is_dir: bool
    children: list[TreeNode] = field(default_factory=list)

# [-----END [200]-----]


# [300] Subsystem: directory walker

# [010] walk a directory and build a TreeNode
# [SCOPE] reads directory entries from the filesystem; returns a TreeNode rooted at the given path. Logs and skips entries that cannot be read.
# [OUT-OF-SCOPE] writes to the filesystem, follows symlinks, raises on individual entry read failures

def walk_tree(
    root: Path,
    filter_fn: Callable[[Path], bool] | None = None,
    max_depth: int | None = None,
) -> TreeNode:
    """Build a TreeNode from a directory on disk.

    Args:
        root: Path to the directory to scan. Must exist and be a directory.
        filter_fn: Optional predicate taking a Path and returning True to include
            the entry, False to exclude. Applied to every entry encountered
            (both files and directories). If None, all entries are included.
        max_depth: Optional maximum recursion depth. None means unlimited.
            0 means only the root entry (no children scanned).
            1 means root plus immediate children, and so on.

    Returns:
        The root TreeNode with populated children.

    Raises:
        InvalidTargetError: If root does not exist or is not a directory.

    Behavior notes:
        - Symlinks are NOT followed. Symlinked directories are recorded as
          leaves with is_dir=False to keep cross-platform behavior predictable.
        - Unreadable directories (PermissionError, OSError) are logged at
          WARNING and recorded with no children. The walk does not abort.
        - Children within a directory are sorted: directories first, then files,
          each alphabetically by lowercased name.
    """

    # [001] validate target
    if not root.exists():
        raise InvalidTargetError(f"Target path does not exist: {root}")
    if not root.is_dir():
        raise InvalidTargetError(f"Target path is not a directory: {root}")
    # [-----END [001]-----]

    # [002] build root node and recurse
    root_node = TreeNode(path=root, name=root.name or str(root), is_dir=True)
    if max_depth is None or max_depth > 0:
        _populate_children(root_node, filter_fn, max_depth, current_depth=1)
    return root_node
    # [-----END [002]-----]

# [-----END [010]-----]


# [020] populate children of a directory node recursively
# [SCOPE] reads child entries of node.path from the filesystem and appends TreeNodes to node.children. Logs and skips entries on read errors.
# [OUT-OF-SCOPE] writes to the filesystem, follows symlinks, raises on individual entry read failures

def _populate_children(
    node: TreeNode,
    filter_fn: Callable[[Path], bool] | None,
    max_depth: int | None,
    current_depth: int,
) -> None:
    """Internal: scan node.path, filter, sort, and recurse into subdirectories.

    Mutates node.children in place. Symlinked directories are NOT recursed into
    to prevent cycles and to keep behavior predictable across platforms.
    """

    # [001] read directory entries; log and skip on read error
    try:
        entries = list(node.path.iterdir())
    except (PermissionError, OSError) as e:
        logger.warning("Cannot read directory %s: %s", node.path, e)
        return
    # [-----END [001]-----]

    # [002] apply filter
    if filter_fn is not None:
        entries = [entry for entry in entries if filter_fn(entry)]
    # [-----END [002]-----]

    # [003] sort: directories first, then files, each alphabetically
    entries.sort(key=lambda p: (not _is_real_dir(p), p.name.lower()))
    # [-----END [003]-----]

    # [004] build child nodes and recurse
    for entry in entries:
        is_dir = _is_real_dir(entry)
        child = TreeNode(path=entry, name=entry.name, is_dir=is_dir)
        node.children.append(child)
        if is_dir and (max_depth is None or current_depth < max_depth):
            _populate_children(child, filter_fn, max_depth, current_depth + 1)
    # [-----END [004]-----]

# [-----END [020]-----]


# [030] determine whether a path is a real directory (not a symlink)
# [SCOPE] reads filesystem stat data to classify the given path; returns True only for non-symlink directories.
# [OUT-OF-SCOPE] writes to the filesystem, raises on classification failure

def _is_real_dir(path: Path) -> bool:
    """Return True if path is a directory AND not a symlink.

    Symlinks (even to directories) are treated as leaves to avoid cycles.
    Stat errors are absorbed and the path is classified as not-a-directory.
    """

    # [001] classify with safe fallback
    try:
        return path.is_dir() and not path.is_symlink()
    except OSError:
        return False
    # [-----END [001]-----]

# [-----END [030]-----]

# [-----END [300]-----]