# [10000] Beacon: tests for the ASCII, CSV, and Mermaid formatters

"""Tests for ascii_tree_tool.backend.formatters.

Covers all three Phase 1 formatters (format_ascii, format_csv, format_mermaid)
and the shared build_generation_header helper. Verifies output shape,
edge cases (empty trees), and cross-formatter consistency (matching
timestamps when called in sequence).

Tests construct TreeNode fixtures directly rather than via walk_tree to keep
formatter tests independent of the walker.
"""

from __future__ import annotations

from pathlib import Path

from ascii_tree_tool.backend.formatters.ascii import (
    build_generation_header,
    format_ascii,
)
from ascii_tree_tool.backend.formatters.csv_fmt import format_csv
from ascii_tree_tool.backend.formatters.mermaid import format_mermaid
from ascii_tree_tool.backend.tree import TreeNode


# [100] Subsystem: test helpers

def _make_test_tree() -> TreeNode:
    """Build a standard test tree: root with two files and one subdirectory.

    Structure:
        myproject/
        +-- sub/
        |   +-- inner.txt
        +-- a.txt
        +-- b.txt
    """

    # [001] construct nested TreeNodes
    inner = TreeNode(
        path=Path("myproject/sub/inner.txt"),
        name="inner.txt",
        is_dir=False,
    )
    sub = TreeNode(
        path=Path("myproject/sub"),
        name="sub",
        is_dir=True,
        children=[inner],
    )
    a = TreeNode(path=Path("myproject/a.txt"), name="a.txt", is_dir=False)
    b = TreeNode(path=Path("myproject/b.txt"), name="b.txt", is_dir=False)
    return TreeNode(
        path=Path("myproject"),
        name="myproject",
        is_dir=True,
        children=[sub, a, b],
    )
    # [-----END [001]-----]


def _make_empty_tree() -> TreeNode:
    """Build a root TreeNode with no children for empty-tree tests."""

    # [001] construct empty root
    return TreeNode(path=Path("empty"), name="empty", is_dir=True)
    # [-----END [001]-----]

# [-----END [100]-----]


# [200] Subsystem: build_generation_header tests

class TestBuildGenerationHeader:
    """Tests for the shared generation header builder."""

    # [010] test that the header contains the expected lines
    def test_contains_timestamp_and_source(self) -> None:
        """build_generation_header returns two lines: timestamp and source."""

        # [001] generate and inspect; use str(Path) so assertion is OS-agnostic
        source = Path("some/path")
        header = build_generation_header(source)
        lines = header.split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("Generated: ")
        assert lines[1].startswith("Source: ")
        assert str(source) in lines[1]
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that the timestamp is ISO 8601 with timezone offset
    def test_timestamp_is_iso8601_with_timezone(self) -> None:
        """The Generated: line carries an ISO 8601 timestamp with timezone offset."""

        # [001] generate and check structure
        header = build_generation_header(Path("."))
        ts_line = header.split("\n")[0]
        ts_value = ts_line.removeprefix("Generated: ")
        # ISO 8601 with offset includes 'T' separator and a '+' or '-' for the tz offset
        assert "T" in ts_value
        assert ("+" in ts_value) or ("-" in ts_value)
        # [-----END [001]-----]

    # [-----END [020]-----]

# [-----END [200]-----]


# [300] Subsystem: format_ascii tests

class TestFormatAscii:
    """Tests for the ASCII tree formatter."""

    # [010] test basic structural elements of the output
    def test_contains_root_and_tree_art(self) -> None:
        """format_ascii output contains the root label and Unicode tree art characters."""

        # [001] format and check
        output = format_ascii(_make_test_tree())
        assert "myproject/" in output
        assert "a.txt" in output
        assert "sub/" in output
        # At least one branch character and one continuation character must appear
        assert "\u251c" in output or "\u2514" in output  # branch markers
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that directories carry a trailing slash
    def test_directories_have_trailing_slash(self) -> None:
        """Directory names in the output are suffixed with '/'."""

        # [001] format and check
        output = format_ascii(_make_test_tree())
        assert "sub/" in output
        # The non-directory entries do NOT carry a trailing slash
        # Check that the line ends right after 'a.txt' (no slash)
        assert "a.txt/" not in output
        assert "b.txt/" not in output
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that the commented header is present and uses '#'
    def test_header_uses_hash_comments(self) -> None:
        """The generation header lines in ASCII output are prefixed with '# '."""

        # [001] format and inspect first lines
        output = format_ascii(_make_test_tree())
        lines = output.split("\n")
        assert lines[0].startswith("# Generated: ")
        assert lines[1].startswith("# Source: ")
        # [-----END [001]-----]

    # [-----END [030]-----]


    # [040] test the empty-tree case
    def test_empty_tree(self) -> None:
        """format_ascii on a root with no children produces a header plus the root label."""

        # [001] format empty tree and check
        output = format_ascii(_make_empty_tree())
        assert "empty/" in output
        # No tree-art characters because there are no children
        assert "\u251c" not in output
        assert "\u2514" not in output
        # [-----END [001]-----]

    # [-----END [040]-----]

# [-----END [300]-----]


# [400] Subsystem: format_csv tests

class TestFormatCsv:
    """Tests for the CSV formatter."""

    # [010] test that the CSV header row is present
    def test_contains_csv_header_row(self) -> None:
        """format_csv output contains the 'path,type,depth' field header."""

        # [001] format and check
        output = format_csv(_make_test_tree())
        assert "path,type,depth" in output
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that the root row is depth 0 type dir
    def test_root_row_is_depth_zero_dir(self) -> None:
        """The root entry appears as path '.', type 'dir', depth 0."""

        # [001] format and check
        output = format_csv(_make_test_tree())
        assert ".,dir,0" in output
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that child rows carry the correct depth values
    def test_child_rows_have_correct_depth(self) -> None:
        """Immediate children of root have depth 1; grandchildren have depth 2."""

        # [001] format and check depth-tagged rows
        output = format_csv(_make_test_tree())
        assert "sub,dir,1" in output
        assert "a.txt,file,1" in output
        assert "b.txt,file,1" in output
        assert "sub/inner.txt,file,2" in output
        # [-----END [001]-----]

    # [-----END [030]-----]


    # [040] test the commented header uses '#'
    def test_header_uses_hash_comments(self) -> None:
        """The generation header lines in CSV output are prefixed with '# '."""

        # [001] format and inspect first two lines (header uses \n; body switches to \r\n)
        output = format_csv(_make_test_tree())
        lines = output.split("\n")
        assert lines[0].startswith("# Generated: ")
        assert lines[1].startswith("# Source: ")
        # [-----END [001]-----]

    # [-----END [040]-----]


    # [050] test RFC 4180 CRLF line terminators
    def test_uses_crlf_line_endings(self) -> None:
        """CSV body lines are separated by CRLF (RFC 4180), not just LF."""

        # [001] format and check for CRLF
        output = format_csv(_make_test_tree())
        assert "\r\n" in output
        # [-----END [001]-----]

    # [-----END [050]-----]


    # [060] test the empty-tree case
    def test_empty_tree(self) -> None:
        """format_csv on a root with no children produces header + schema row + one data row."""

        # [001] format empty tree and check
        output = format_csv(_make_empty_tree())
        assert "path,type,depth" in output
        assert ".,dir,0" in output
        # [-----END [001]-----]

    # [-----END [060]-----]

# [-----END [400]-----]


# [500] Subsystem: format_mermaid tests

class TestFormatMermaid:
    """Tests for the Mermaid flowchart formatter."""

    # [010] test that the flowchart declaration is present
    def test_contains_flowchart_declaration(self) -> None:
        """format_mermaid output begins (after header) with 'flowchart TD'."""

        # [001] format and check
        output = format_mermaid(_make_test_tree())
        assert "flowchart TD" in output
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that node IDs are sanitized and prefixed with 'n_'
    def test_node_ids_sanitized_and_prefixed(self) -> None:
        """Path components produce node IDs starting with 'n_' and containing no dots or slashes."""

        # [001] format and check ID format
        output = format_mermaid(_make_test_tree())
        # Root uses relative path '.' which sanitizes to '_'; ID is 'n__'.
        # The root's actual name appears in the label, not the ID.
        assert "n__" in output
        # The 'sub' subdirectory has relative path 'sub' giving ID 'n_sub'.
        assert "n_sub" in output
        # 'sub/inner.txt' becomes 'n_sub_inner_txt' (forward slash sanitized to underscore).
        assert "n_sub_inner_txt" in output
        # Sanitized IDs themselves contain no dots or slashes
        for line in output.split("\n"):
            stripped = line.strip()
            if stripped.startswith("n_") and "[" in stripped:
                node_id = stripped.split("[")[0]
                assert "." not in node_id
                assert "/" not in node_id
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that edges connect parents to children
    def test_contains_parent_child_edges(self) -> None:
        """Edges of the form 'parent --> child' link the root to its children."""

        # [001] format and check for the arrow operator
        output = format_mermaid(_make_test_tree())
        assert "-->" in output
        # The root (ID 'n__', since the root's relative path is '.') has at least one outgoing edge
        assert "n__ -->" in output
        # [-----END [001]-----]

    # [-----END [030]-----]


    # [040] test that the commented header uses '%%'
    def test_header_uses_double_percent_comments(self) -> None:
        """The generation header lines in Mermaid output are prefixed with '%% '."""

        # [001] format and inspect first lines
        output = format_mermaid(_make_test_tree())
        lines = output.split("\n")
        assert lines[0].startswith("%% Generated: ")
        assert lines[1].startswith("%% Source: ")
        # [-----END [001]-----]

    # [-----END [040]-----]


    # [050] test the empty-tree case
    def test_empty_tree(self) -> None:
        """format_mermaid on a root with no children produces a one-node diagram, no edges."""

        # [001] format empty tree and check
        output = format_mermaid(_make_empty_tree())
        assert "flowchart TD" in output
        # Root ID is 'n__' (sanitized '.'); root name appears in the label, not the ID
        assert "n__" in output
        assert "empty/" in output
        assert "-->" not in output
        # [-----END [001]-----]

    # [-----END [050]-----]

# [-----END [500]-----]


# [600] Subsystem: cross-formatter consistency tests

class TestFormatterConsistency:
    """Tests for invariants that span multiple formatters."""

    # [010] test that all three formatters produce matching timestamps when called in sequence
    def test_timestamps_match_across_formatters(self) -> None:
        """Headers from all three formatters carry the same timestamp when called in quick succession."""

        # [001] call all three on the same tree and extract timestamps
        # All three formatters use \n between Generated/Source lines in the header,
        # so we can split by \n uniformly even though CSV body uses \r\n.
        tree = _make_test_tree()
        ascii_output = format_ascii(tree)
        csv_output = format_csv(tree)
        mermaid_output = format_mermaid(tree)

        ascii_ts = ascii_output.split("\n")[0].removeprefix("# Generated: ")
        csv_ts = csv_output.split("\n")[0].removeprefix("# Generated: ")
        mermaid_ts = mermaid_output.split("\n")[0].removeprefix("%% Generated: ")
        # [-----END [001]-----]

        # [002] verify all three timestamps match to the second
        assert ascii_ts == csv_ts == mermaid_ts
        # [-----END [002]-----]

    # [-----END [010]-----]


    # [020] test that all three formatters handle the empty tree without error
    def test_all_formatters_handle_empty_tree(self) -> None:
        """All three formatters return non-empty strings when given an empty tree."""

        # [001] format empty tree with each formatter
        empty = _make_empty_tree()
        assert len(format_ascii(empty)) > 0
        assert len(format_csv(empty)) > 0
        assert len(format_mermaid(empty)) > 0
        # [-----END [001]-----]

    # [-----END [020]-----]

# [-----END [600]-----]