# [10000] Beacon: CSV formatter for tree output

"""CSV formatter.

Renders a TreeNode as a CSV string with three columns: path, type, depth.

The output begins with a commented preamble (timestamp and source path, each
line prefixed with '#'), followed by a standard CSV header row and one data
row per entry. The root entry is included as row 0 (depth 0, type 'dir').

Paths use forward slashes regardless of OS for portability. Line terminators
are CRLF per RFC 4180 for cross-platform diff consistency.
"""

from __future__ import annotations

import csv
import io
from pathlib import PurePosixPath

from ascii_tree_tool.backend.formatters.ascii import build_generation_header
from ascii_tree_tool.backend.tree import TreeNode

_FIELDNAMES = ("path", "type", "depth")


# [100] Subsystem: CSV rendering

# [010] render a TreeNode as a complete CSV string
# [SCOPE] returns the full CSV text including a commented generation header and rendered data rows. 
#         Reads the system clock via the header helper. No filesystem access.
# [OUT-OF-SCOPE] filesystem reads or writes, walking the tree, emitting non-RFC-4180 line terminators

def format_csv(node: TreeNode) -> str:
    """Render a TreeNode as a CSV string.

    The returned string has three regions:
        1. A commented generation header (timestamp and source path), each
           line prefixed with '# '. Standard CSV consumers either skip these
           via comment-prefix support or ignore them as malformed rows.
        2. A header row: 'path,type,depth'.
        3. One data row per entry, depth-first, with the root as row 0.

    Args:
        node: The root TreeNode to render. Typically the result of walk_tree().

    Returns:
        A CSV-formatted string with CRLF line terminators. Includes a trailing
        CRLF after the final row per RFC 4180.

    Notes:
        - Paths are relative to the root node, using forward slashes for
          portability. The root itself appears as path '.'.
        - 'type' is exactly 'dir' or 'file'. Symlinks are recorded with their
          classified type (typically 'file' because the walker does not follow
          them).
        - 'depth' is an integer with the root at 0.
    """

    # [001] build the commented header
    header_text = build_generation_header(node.path)
    commented_header = "\n".join(f"# {line}" for line in header_text.split("\n"))
    # [-----END [001]-----]

    # [002] write CSV body to in-memory buffer
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(_FIELDNAMES)
    _write_node_rows(writer, node, parent_path=None, depth=0)
    csv_body = buffer.getvalue()
    # [-----END [002]-----]

    # [003] assemble final output: commented header, blank line, CSV body
    return f"{commented_header}\r\n\r\n{csv_body}"
    # [-----END [003]-----]

# [-----END [010]-----]


# [020] write CSV rows for a node and its descendants
# [SCOPE] writes one CSV row per node in a depth-first traversal, each row containing relative path, 
#         type, and depth. Pure transformation; no I/O beyond the supplied writer.
# [OUT-OF-SCOPE] filesystem reads or writes, modifying the input nodes, walking the filesystem

def _write_node_rows(
    writer: csv.writer,
    node: TreeNode,
    parent_path: PurePosixPath | None,
    depth: int,
) -> None:
    """Internal: write one row for node, then recurse into its children.

    Args:
        writer: A csv.writer bound to the output buffer.
        node: The TreeNode to emit a row for, then recurse into.
        parent_path: The forward-slash path accumulated from ancestors, or
            None when emitting the root row.
        depth: The depth of this node, with the root at 0.
    """

    # [001] compose the relative path for this row
    if parent_path is None:
        relative_path = PurePosixPath(".")
    else:
        relative_path = parent_path / node.name
    # [-----END [001]-----]

    # [002] write this node's row
    type_label = "dir" if node.is_dir else "file"
    writer.writerow((str(relative_path), type_label, depth))
    # [-----END [002]-----]

    # [003] recurse into children
    for child in node.children:
        _write_node_rows(writer, child, relative_path, depth + 1)
    # [-----END [003]-----]

# [-----END [020]-----]

# [-----END [100]-----]