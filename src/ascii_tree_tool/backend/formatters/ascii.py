# [10000] Beacon: ASCII tree formatter and shared generation header

"""Tree formatter (conventional 'ASCII tree' format).

Renders a TreeNode using Unicode box-drawing characters in the conventional
'tree' command style. Output is suitable for .txt files, GUI preview, and
pasting into READMEs or AI uploads. The 'ascii' module name is a convention;
operator explicitly opted in to Unicode output per the project's
ASCII-by-default discipline.

Also defines build_generation_header, the shared header builder used by all
formatters to prefix output with a timestamp and source-path banner. Each
formatter wraps the header text in its own comment carrier.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ascii_tree_tool.backend.tree import TreeNode

# Box-drawing characters for tree art. Unicode per explicit operator opt-in.
_BRANCH_MID = "\u251c\u2500\u2500 "    # entry marker for middle siblings
_BRANCH_LAST = "\u2514\u2500\u2500 "   # entry marker for the last sibling
_PIPE = "\u2502   "                    # vertical continuation when more siblings follow
_BLANK = "    "                        # blank continuation when no more siblings follow


# [100] Subsystem: generation header

# [010] build the shared generation header for any formatter
# [SCOPE] returns a multi-line header string with timestamp and source path. Reads the system clock; does not read or write the filesystem.
# [OUT-OF-SCOPE] filesystem reads or writes, format-specific comment carriers, locale-specific timestamp formatting

def build_generation_header(source_path: Path) -> str:
    """Return a two-line generation header for embedding in formatter output.

    The returned text has no comment carrier prefix; each formatter is
    responsible for wrapping the lines in its own comment syntax (e.g., # for
    ASCII/CSV, %% for Mermaid).

    Args:
        source_path: The target directory the tree was generated from. Used
            verbatim; no resolution or normalization is performed.

    Returns:
        A two-line string: a timestamp line and a source-path line, separated
        by a single newline. No trailing newline.
    """

    # [001] read system clock with local timezone
    now = datetime.now().astimezone()
    timestamp = now.isoformat(timespec="seconds")
    # [-----END [001]-----]

    # [002] compose and return header
    return f"Generated: {timestamp}\nSource: {source_path}"
    # [-----END [002]-----]

# [-----END [010]-----]

# [-----END [100]-----]


# [200] Subsystem: ASCII tree rendering

# [010] render a TreeNode as a complete ASCII tree string
# [SCOPE] returns the full ASCII tree text including a commented generation header and the rendered tree art. Reads the system clock via the header helper. No filesystem access.
# [OUT-OF-SCOPE] filesystem reads or writes, walking the tree

def format_ascii(node: TreeNode) -> str:
    """Render a TreeNode as an ASCII tree string.

    The returned string has three regions:
        1. A commented generation header (timestamp and source path), each
           line prefixed with '# '.
        2. A blank line.
        3. The root node's name as a header line (e.g., 'ascii-tree-tool/'),
           followed by its children rendered with conventional tree-art prefixes
           (mid-branch, last-branch, pipe-continuation, blank).

    Args:
        node: The root TreeNode to render. Typically the result of walk_tree().

    Returns:
        A newline-terminated string ready to write to a .txt file or display
        in a GUI text widget. Lines are joined with '\\n'; no trailing newline
        beyond the final entry.

    Notes:
        - Directories are suffixed with '/' for visual disambiguation.
        - Tree art uses Unicode box-drawing characters matching the conventional
          'tree' command output (and what AI assistants natively produce/consume).
        - Long entry names are not wrapped; the caller chooses any line-length
          handling at the display layer.
    """

    # [001] build the commented header
    header_text = build_generation_header(node.path)
    commented_header = "\n".join(f"# {line}" for line in header_text.split("\n"))
    # [-----END [001]-----]

    # [002] render root and children
    root_label = _label_for(node)
    body_lines = _render_children(node.children, prefix="")
    # [-----END [002]-----]

    # [003] assemble final output
    parts = [commented_header, "", root_label]
    parts.extend(body_lines)
    return "\n".join(parts)
    # [-----END [003]-----]

# [-----END [010]-----]


# [020] render a list of sibling children with a given indentation prefix
# [SCOPE] returns the list of rendered lines for a child sequence. Pure transformation; no filesystem access, no I/O.
# [OUT-OF-SCOPE] filesystem reads or writes, modifying the input nodes

def _render_children(children: list[TreeNode], prefix: str) -> list[str]:
    """Internal: render a list of sibling TreeNodes as indented tree lines.

    Args:
        children: The sibling nodes to render in order.
        prefix: The indentation string inherited from ancestor levels (composed
            of _PIPE and _BLANK segments from each ancestor depth).

    Returns:
        Flat list of rendered lines. Empty list if children is empty.
    """

    # [001] short-circuit empty sibling lists
    if not children:
        return []
    # [-----END [001]-----]

    # [002] render each child and recurse into its subtree
    lines: list[str] = []
    last_index = len(children) - 1
    for index, child in enumerate(children):
        is_last = index == last_index
        branch = _BRANCH_LAST if is_last else _BRANCH_MID
        lines.append(f"{prefix}{branch}{_label_for(child)}")
        if child.children:
            # If this child has more siblings after it, descendants need a pipe
            # for continuity; if it is the last sibling, descendants get blank.
            continuation = _BLANK if is_last else _PIPE
            lines.extend(_render_children(child.children, prefix + continuation))
    return lines
    # [-----END [002]-----]

# [-----END [020]-----]


# [030] format a node's display label
# [SCOPE] returns the display label string for a TreeNode (name with trailing slash for directories). Pure transformation; no I/O.
# [OUT-OF-SCOPE] filesystem reads or writes, escaping of special characters in names

def _label_for(node: TreeNode) -> str:
    """Internal: return the node's display label with a trailing slash for dirs."""

    # [001] apply directory suffix convention
    return f"{node.name}/" if node.is_dir else node.name
    # [-----END [001]-----]

# [-----END [030]-----]

# [-----END [200]-----]