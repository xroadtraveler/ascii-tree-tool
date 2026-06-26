# ascii-tree-tool

> **Status:** Alpha — Phase 1 in active development.

Cross-platform desktop GUI for generating ASCII tree representations of folder structures, with `.txt`, `.csv`, and Mermaid export.

## Why?

The standard `tree` command works fine on the command line, but generating a tree to drop into project documentation typically means copy-pasting terminal output and cleaning it up by hand. `ascii-tree-tool` produces clean, documentation-ready snapshots through a GUI, with multiple export formats for different downstream uses:

- **`.txt`** — paste into a `README.md` code block, or hand to an AI assistant as project context.
- **`.csv`** — programmatic consumption, spreadsheet inspection.
- **Mermaid** — embed as a rendered diagram in Markdown that supports Mermaid (GitHub, GitLab, MkDocs, etc.).

## Features (Phase 1)

- Point-and-click target directory selection.
- Configurable output location (defaults to one level above the target folder).
- Visual preview of the generated tree before export.
- Three export formats: ASCII `.txt` (default), `.csv`, Mermaid.
- Generation header with timestamp and source path on every export.
- Timestamped output filenames to prevent accidental overwrites.
- Default exclusion of `.git/` and `__pycache__/` (toggleable via checkboxes).
- CLI launch hook: `python -m ascii_tree_tool --target /some/path`.

## Requirements

- Python 3.10 or newer.
- Operating system: Windows or Linux. macOS likely works but is currently untested.

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/xroadtraveler/ascii-tree-tool.git
cd ascii-tree-tool
pip install -e .
```

For development (includes `pytest` and `pytest-qt`):

```bash
pip install -e ".[dev]"
```

## Usage

Launch the GUI:

```bash
ascii-tree-tool
```

Or, equivalently:

```bash
python -m ascii_tree_tool
```

To pre-populate the target directory at launch (useful for shell integrations):

```bash
python -m ascii_tree_tool --target /path/to/your/project
```

## Roadmap

Planned for Phase 2:

- Interactive visualizer (expand/collapse nodes, right-click open).
- Per-language exclusion presets (Python, Node, Rust, Go) with custom glob patterns and `.gitignore` respect.
- Per-directory annotations that render as inline comments, persisting across regenerations.
- Additional export formats: Markdown, SVG/PNG, HTML.
- Windows Explorer / Linux file manager shell context menu integration.
- "Update" mode: diff a fresh scan against a previous snapshot.

Planned for Phase 3:

- Sketch mode: build a tree by typing rather than scanning a real directory, for pre-code architectural planning.

## License

Apache License 2.0 — see [LICENSE](LICENSE).