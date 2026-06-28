# [10000] Beacon: Mermaid flowchart formatter for tree output

"""Mermaid flowchart formatter.

Renders a TreeNode as a Mermaid 'flowchart TD' (top-down) diagram suitable
for embedding in Markdown documents that support Mermaid rendering (GitHub,
GitLab, MkDocs, Obsidian, etc.).

Node IDs are derived from path components with non-alphanumeric characters
replaced by underscores, guaranteeing valid Mermaid syntax while keeping the
generated source readable. Node labels show only the basename; hierarchy is
encoded by edges. Directories are visually disambiguated by a trailing slash
in the label.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from ascii_tree_tool.backend.formatters.ascii import build_generation_header
from ascii_tree_tool.backend.tree import TreeNode

# Pre-compiled regex for sanitizing path components into Mermaid-safe node IDs.
_ID_SANITIZER = re.compile(r"[^a-zA-Z0-9_]")


# [100] Subsystem: Mermaid rendering

# [010] render a TreeNode as a complete Mermaid diagram string
# [SCOPE] returns a Mermaid flowchart TD diagram including a generation header in Mermaid comment syntax. 
#         Reads the system clock via the header helper. No filesystem access.
# [OUT-OF-SCOPE] filesystem reads or writes, walking the tree, emitting non-Mermaid output formats

def format_mermaid(node: TreeNode) -> str:
    """Render a TreeNode as a Mermaid flowchart TD diagram.

    The returned string has four regions:
        1. A generation header in Mermaid comment syntax, each line prefixed
           with '%% '.
        2. The 'flowchart TD' diagram declaration.
        3. Node definitions, one per entry, with sanitized IDs and basename
           labels (directories include a trailing slash in the label).
        4. Edge definitions connecting each parent to its children with '-->'.

    Args:
        node: The root TreeNode to render. Typically the result of walk_tree().

    Returns:
        A Mermaid-source string suitable for saving as a '.mermaid' file or
        embedding inside a fenced Markdown code block tagged 'mermaid'.

    Notes:
        - Node IDs are derived from path components with non-alphanumeric
          characters replaced by underscores. Collisions are not expected
          for realistic filesystems but are theoretically possible; if a
          collision occurs the resulting diagram will be malformed.
        - An empty tree (root with no children) produces a valid one-node
          diagram, not an empty string.
    """

    # [001] build the Mermaid-commented header
    header_text = build_generation_header(node.path)
    commented_header = "\n".join(f"%% {line}" for line in header_text.split("\n"))
    # [-----END [001]-----]

    # [002] collect node definitions and edge definitions via traversal
    node_defs: list[str] = []
    edge_defs: list[str] = []
    _walk_for_mermaid(
        node=node,
        parent_path=None,
        parent_id=None,
        node_defs=node_defs,
        edge_defs=edge_defs,
    )
    # [-----END [002]-----]

    # [003] assemble final output
    lines = [commented_header, "", "flowchart TD"]
    lines.extend(f"    {definition}" for definition in node_defs)
    lines.extend(f"    {edge}" for edge in edge_defs)
    return "\n".join(lines)
    # [-----END [003]-----]

# [-----END [010]-----]


# [020] traverse the tree collecting Mermaid node and edge definitions
# [SCOPE] populates the supplied node_defs and edge_defs lists with Mermaid syntax for the given node 
#         and its descendants. Pure transformation; no I/O.
# [OUT-OF-SCOPE] filesystem reads or writes, modifying the input TreeNode

def _walk_for_mermaid(
    node: TreeNode,
    parent_path: PurePosixPath | None,
    parent_id: str | None,
    node_defs: list[str],
    edge_defs: list[str],
) -> None:
    """Internal: walk the tree, appending Mermaid node and edge syntax.

    Args:
        node: The TreeNode to process.
        parent_path: The forward-slash path accumulated from ancestors, or
            None when processing the root.
        parent_id: The sanitized Mermaid ID of the parent node, or None when
            processing the root.
        node_defs: Output list to append node definitions to.
        edge_defs: Output list to append edge definitions to.
    """

    # [001] compose the relative path and sanitized ID for this node
    if parent_path is None:
        relative_path = PurePosixPath(".")
    else:
        relative_path = parent_path / node.name
    node_id = _sanitize_id(str(relative_path))
    # [-----END [001]-----]

    # [002] emit this node's definition
    label = f"{node.name}/" if node.is_dir else node.name
    # Use the literal node.name (or '.' for the root) so the label matches the
    # tree the user sees, not the sanitized ID. Mermaid quotes the label.
    label_text = label if parent_path is not None else f"{node.name or '.'}/"
    node_defs.append(f'{node_id}["{label_text}"]')
    # [-----END [002]-----]

    # [003] emit the edge from parent if this is not the root
    if parent_id is not None:
        edge_defs.append(f"{parent_id} --> {node_id}")
    # [-----END [003]-----]

    # [004] recurse into children
    for child in node.children:
        _walk_for_mermaid(
            node=child,
            parent_path=relative_path,
            parent_id=node_id,
            node_defs=node_defs,
            edge_defs=edge_defs,
        )
    # [-----END [004]-----]

# [-----END [020]-----]


# [030] sanitize a path string into a Mermaid-safe node ID
# [SCOPE] returns a string with all non-alphanumeric, non-underscore characters replaced by underscores, 
#         prefixed with 'n_' to guarantee a letter start. Pure transformation; no I/O.
# [OUT-OF-SCOPE] filesystem reads or writes, collision detection between sanitized IDs

def _sanitize_id(path_str: str) -> str:
    """Internal: convert an arbitrary path string into a valid Mermaid node ID.

    Mermaid node IDs must start with a letter and contain only alphanumeric
    characters and underscores. This function replaces every disallowed
    character with an underscore and prefixes with 'n_' to guarantee a valid
    starting character.

    Args:
        path_str: The path string to sanitize (any characters allowed).

    Returns:
        A string matching the pattern n_[a-zA-Z0-9_]+.
    """

    # [001] sanitize and prefix
    sanitized = _ID_SANITIZER.sub("_", path_str)
    return f"n_{sanitized}"
    # [-----END [001]-----]

# [-----END [030]-----]

# [-----END [100]-----]