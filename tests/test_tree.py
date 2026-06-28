# [10000] Beacon: tests for the tree walker module

"""Tests for ascii_tree_tool.backend.tree.

Covers TreeNode dataclass construction and walk_tree behavior across the
happy path and major edge cases: max_depth, filter_fn, sort order, empty
directories, and invalid targets. Symlink and permission-denied tests are
deferred to Phase 2 polish due to platform-specific test setup requirements.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ascii_tree_tool.backend.tree import (
    ASCIITreeToolError,
    InvalidTargetError,
    TreeNode,
    walk_tree,
)


# [100] Subsystem: test helpers

def _make_tree(root: Path, structure: dict) -> None:
    """Build a directory tree from a nested dict spec.

    Keys ending in '/' are directories; their values are nested dicts of the
    same shape. Other keys are files; their values are file contents (str)
    or anything falsy for empty files.
    """

    # [001] iterate the spec and create entries
    for name, content in structure.items():
        if name.endswith("/"):
            subdir = root / name.rstrip("/")
            subdir.mkdir()
            if isinstance(content, dict):
                _make_tree(subdir, content)
        else:
            file_content = content if isinstance(content, str) else ""
            (root / name).write_text(file_content)
    # [-----END [001]-----]

# [-----END [100]-----]


# [200] Subsystem: TreeNode dataclass tests

class TestTreeNode:
    """Tests for the TreeNode dataclass."""

    # [010] test basic construction with required fields
    def test_basic_construction(self) -> None:
        """TreeNode accepts required fields and defaults children to []."""

        # [001] construct and verify
        node = TreeNode(path=Path("foo"), name="foo", is_dir=True)
        assert node.path == Path("foo")
        assert node.name == "foo"
        assert node.is_dir is True
        assert node.children == []
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test construction with explicit children
    def test_with_children(self) -> None:
        """TreeNode accepts and stores a children list."""

        # [001] construct parent with one child
        child = TreeNode(path=Path("foo/bar"), name="bar", is_dir=False)
        parent = TreeNode(
            path=Path("foo"), name="foo", is_dir=True, children=[child]
        )
        assert len(parent.children) == 1
        assert parent.children[0] is child
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that each TreeNode gets its own children list (no shared mutable default)
    def test_children_default_is_not_shared(self) -> None:
        """Two TreeNodes with default children do not share the same list."""

        # [001] construct two and mutate one
        a = TreeNode(path=Path("a"), name="a", is_dir=True)
        b = TreeNode(path=Path("b"), name="b", is_dir=True)
        a.children.append(TreeNode(path=Path("a/x"), name="x", is_dir=False))
        assert len(a.children) == 1
        assert len(b.children) == 0
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [200]-----]


# [300] Subsystem: walk_tree happy path tests

class TestWalkTreeHappyPath:
    """Tests for normal walk_tree usage on well-formed directories."""

    # [010] test walking a flat directory of files
    def test_walks_flat_directory(self, tmp_path: Path) -> None:
        """walk_tree returns a root with all file children, no recursion."""

        # [001] populate and walk
        _make_tree(tmp_path, {"a.txt": "", "b.txt": "", "c.txt": ""})
        root = walk_tree(tmp_path)
        assert root.is_dir is True
        assert [c.name for c in root.children] == ["a.txt", "b.txt", "c.txt"]
        assert all(not c.is_dir for c in root.children)
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test walking a nested directory
    def test_walks_nested_directory(self, tmp_path: Path) -> None:
        """walk_tree recurses into subdirectories and populates their children."""

        # [001] populate with one subdirectory containing a file
        _make_tree(tmp_path, {"sub/": {"inner.txt": ""}, "file.txt": ""})
        root = walk_tree(tmp_path)
        # Directories sort before files
        assert root.children[0].name == "sub"
        assert root.children[0].is_dir is True
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].name == "inner.txt"
        assert root.children[0].children[0].is_dir is False
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test the sort order: dirs first, then files, alphabetical case-insensitive
    def test_sort_order(self, tmp_path: Path) -> None:
        """Children sort: directories first, then files, each case-insensitive alphabetical."""

        # [001] populate with mixed case and types
        _make_tree(tmp_path, {
            "Zfile.txt": "",
            "afile.txt": "",
            "Mdir/": {},
            "bdir/": {},
        })
        root = walk_tree(tmp_path)
        names = [c.name for c in root.children]
        assert names == ["bdir", "Mdir", "afile.txt", "Zfile.txt"]
        # [-----END [001]-----]

    # [-----END [030]-----]


    # [040] test walking an empty directory
    def test_empty_directory(self, tmp_path: Path) -> None:
        """walk_tree on an empty directory returns a root with no children."""

        # [001] walk without populating
        root = walk_tree(tmp_path)
        assert root.is_dir is True
        assert root.children == []
        # [-----END [001]-----]

    # [-----END [040]-----]

# [-----END [300]-----]


# [400] Subsystem: walk_tree max_depth tests

class TestWalkTreeMaxDepth:
    """Tests for the max_depth parameter."""

    # [010] test max_depth=0 returns only the root
    def test_max_depth_zero(self, tmp_path: Path) -> None:
        """max_depth=0 returns the root with no children scanned."""

        # [001] populate and walk with depth 0
        _make_tree(tmp_path, {"a.txt": "", "sub/": {"inner.txt": ""}})
        root = walk_tree(tmp_path, max_depth=0)
        assert root.children == []
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test max_depth=1 returns root + immediate children only
    def test_max_depth_one(self, tmp_path: Path) -> None:
        """max_depth=1 returns immediate children but does not recurse into subdirs."""

        # [001] populate and walk with depth 1
        _make_tree(tmp_path, {"a.txt": "", "sub/": {"inner.txt": ""}})
        root = walk_tree(tmp_path, max_depth=1)
        assert len(root.children) == 2
        sub = next(c for c in root.children if c.name == "sub")
        assert sub.is_dir is True
        assert sub.children == []
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test max_depth=None means unlimited
    def test_max_depth_none_is_unlimited(self, tmp_path: Path) -> None:
        """max_depth=None recurses to arbitrary depth."""

        # [001] populate three levels deep and walk
        _make_tree(tmp_path, {
            "sub/": {"deeper/": {"deepest/": {"file.txt": ""}}},
        })
        root = walk_tree(tmp_path, max_depth=None)
        deepest = root.children[0].children[0].children[0]
        assert deepest.name == "deepest"
        assert len(deepest.children) == 1
        assert deepest.children[0].name == "file.txt"
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [400]-----]


# [500] Subsystem: walk_tree filter tests

class TestWalkTreeFilter:
    """Tests for the filter_fn parameter."""

    # [010] test that the filter excludes matching entries
    def test_filter_excludes_matching_entries(self, tmp_path: Path) -> None:
        """filter_fn returning False excludes the entry; subdirs are recursed into if filter allows."""

        # [001] populate with mixed entries; filter excludes any name containing 'drop'
        _make_tree(tmp_path, {
            "keep.txt": "",
            "drop.txt": "",
            "sub/": {"also_drop.txt": ""},
        })
        root = walk_tree(tmp_path, filter_fn=lambda p: "drop" not in p.name)
        names = [c.name for c in root.children]
        assert "drop.txt" not in names
        assert "keep.txt" in names
        assert "sub" in names
        # sub/ was included; its only child was filtered out
        sub = next(c for c in root.children if c.name == "sub")
        assert sub.is_dir is True
        assert sub.children == []
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that None filter includes everything
    def test_filter_none_includes_everything(self, tmp_path: Path) -> None:
        """filter_fn=None means no filtering; all entries are included."""

        # [001] populate and walk with no filter
        _make_tree(tmp_path, {"a.txt": "", "b.txt": "", "c.txt": ""})
        root = walk_tree(tmp_path, filter_fn=None)
        assert len(root.children) == 3
        # [-----END [001]-----]

    # [-----END [020]-----]

# [-----END [500]-----]


# [600] Subsystem: walk_tree invalid target tests

class TestWalkTreeInvalidTarget:
    """Tests for the InvalidTargetError cases."""

    # [010] test that a nonexistent path raises InvalidTargetError
    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        """walk_tree on a path that does not exist raises InvalidTargetError."""

        # [001] attempt to walk a missing path
        bad = tmp_path / "does_not_exist"
        with pytest.raises(InvalidTargetError, match="does not exist"):
            walk_tree(bad)
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that a file path raises InvalidTargetError
    def test_file_path_raises(self, tmp_path: Path) -> None:
        """walk_tree on a path that is a file (not a directory) raises InvalidTargetError."""

        # [001] create a file and attempt to walk it
        file_path = tmp_path / "file.txt"
        file_path.write_text("")
        with pytest.raises(InvalidTargetError, match="not a directory"):
            walk_tree(file_path)
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test the exception hierarchy
    def test_invalid_target_error_inherits_from_base(self) -> None:
        """InvalidTargetError is a subclass of ASCIITreeToolError, which is a subclass of Exception."""

        # [001] verify inheritance chain
        assert issubclass(InvalidTargetError, ASCIITreeToolError)
        assert issubclass(ASCIITreeToolError, Exception)
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [600]-----]