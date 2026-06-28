# [10000] Beacon: end-to-end smoke test for the full backend pipeline

"""End-to-end smoke test.

Verifies that the full backend pipeline (walk_tree -> all three formatters
-> file writes -> readback) works correctly on a realistic temporary
directory structure. This is the integration test that catches regressions
spanning module boundaries that unit tests cannot detect.

Run explicitly with:
    pytest tests/smoke_test.py -v -s

The filename does NOT begin with 'test_' so pytest's default discovery
does not pick it up alongside the fast unit tests. Run it deliberately
when you want full end-to-end verification.
"""

from __future__ import annotations

from pathlib import Path

from ascii_tree_tool.backend.filters import default_phase1_filter
from ascii_tree_tool.backend.formatters.ascii import format_ascii
from ascii_tree_tool.backend.formatters.csv_fmt import format_csv
from ascii_tree_tool.backend.formatters.mermaid import format_mermaid
from ascii_tree_tool.backend.tree import walk_tree


# [100] Subsystem: test helpers

def _build_realistic_project(root: Path) -> None:
    """Populate a temp directory with a realistic small project structure.

    Includes the three Phase 1 default-exclusion targets so that filter
    behavior can be verified end-to-end.

    Structure:
        myproject/
        +-- .git/                       (excluded by default filter)
        |   +-- HEAD
        +-- __pycache__/                (excluded by default filter)
        |   +-- cached.pyc
        +-- .venv/                      (excluded by default filter)
        |   +-- pyvenv.cfg
        +-- src/
        |   +-- main.py
        +-- tests/
        |   +-- test_main.py
        +-- README.md
    """

    # [001] create the included directories and their files
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("# placeholder\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text("# placeholder\n")
    (root / "README.md").write_text("# placeholder\n")
    # [-----END [001]-----]

    # [002] create the excluded directories and their files
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "cached.pyc").write_text("")
    (root / ".venv").mkdir()
    (root / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n")
    # [-----END [002]-----]

# [-----END [100]-----]


# [200] Subsystem: end-to-end smoke test

# [010] full pipeline: build, walk, format, write, read back, assert
def test_full_pipeline_end_to_end(tmp_path: Path) -> None:
    """End-to-end: build a project, walk and format it, write all three files, verify contents.

    This test exercises every backend module in sequence and verifies that
    the output files contain the expected markers. Slow relative to unit
    tests but invaluable for catching integration regressions.
    """

    # [001] build the realistic temp project
    project_root = tmp_path / "myproject"
    project_root.mkdir()
    _build_realistic_project(project_root)
    print(f"\nBuilt test project at {project_root}")
    # [-----END [001]-----]

    # [002] walk with the Phase 1 default filter
    root_node = walk_tree(project_root, filter_fn=default_phase1_filter())
    print(f"Walked tree: {len(root_node.children)} top-level entries after filtering")
    # [-----END [002]-----]

    # [003] verify the filter excluded the three default targets
    child_names = [c.name for c in root_node.children]
    assert ".git" not in child_names, "default filter should exclude .git/"
    assert "__pycache__" not in child_names, "default filter should exclude __pycache__/"
    assert ".venv" not in child_names, "default filter should exclude .venv/"
    # And the expected entries ARE present
    assert "src" in child_names
    assert "tests" in child_names
    assert "README.md" in child_names
    print("Filter behavior verified")
    # [-----END [003]-----]

    # [004] format all three outputs
    ascii_output = format_ascii(root_node)
    csv_output = format_csv(root_node)
    mermaid_output = format_mermaid(root_node)
    print("All three formats generated")
    # [-----END [004]-----]

    # [005] write all three to disk in the tmp_path output area
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    ascii_file = output_dir / "tree.txt"
    csv_file = output_dir / "tree.csv"
    mermaid_file = output_dir / "tree.mermaid"
    ascii_file.write_text(ascii_output, encoding="utf-8")
    csv_file.write_text(csv_output, encoding="utf-8")
    mermaid_file.write_text(mermaid_output, encoding="utf-8")
    print(f"Wrote three output files to {output_dir}")
    # [-----END [005]-----]

    # [006] read back and verify ASCII content
    ascii_readback = ascii_file.read_text(encoding="utf-8")
    assert ascii_readback.startswith("# Generated: ")
    assert "myproject/" in ascii_readback
    assert "src/" in ascii_readback
    assert "main.py" in ascii_readback
    assert "README.md" in ascii_readback
    assert ".git" not in ascii_readback
    assert "__pycache__" not in ascii_readback
    print("ASCII output verified")
    # [-----END [006]-----]

    # [007] read back and verify CSV content
    csv_readback = csv_file.read_text(encoding="utf-8")
    assert csv_readback.startswith("# Generated: ")
    assert "path,type,depth" in csv_readback
    assert ".,dir,0" in csv_readback
    assert "src,dir,1" in csv_readback
    assert "src/main.py,file,2" in csv_readback
    assert "README.md,file,1" in csv_readback
    assert ".git" not in csv_readback
    print("CSV output verified")
    # [-----END [007]-----]

    # [008] read back and verify Mermaid content
    mermaid_readback = mermaid_file.read_text(encoding="utf-8")
    assert mermaid_readback.startswith("%% Generated: ")
    assert "flowchart TD" in mermaid_readback
    assert "n__" in mermaid_readback
    assert "n_src" in mermaid_readback
    assert "n_src_main_py" in mermaid_readback
    assert "-->" in mermaid_readback
    assert ".git" not in mermaid_readback
    print("Mermaid output verified")
    # [-----END [008]-----]

    print("End-to-end smoke test passed.")

# [-----END [010]-----]

# [-----END [200]-----]