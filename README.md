# ascii-tree-tool

> **Status:** Alpha — Phase 1 complete; Phase 2 in planning.

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

- **For the pre-built Windows executable:** Windows 10 or newer. No other requirements — Python and PyQt6 are bundled inside the .exe.
- **For installing from source:** Python 3.10 or newer. Any OS that supports PyQt6 (Windows, Linux, macOS).

## Installation

### Download the pre-built executable (Windows)

Grab the latest `ascii-tree-tool.exe` from the [Releases page](https://github.com/xroadtraveler/ascii-tree-tool/releases/latest). Double-click to run — no installation, no Python required.

Pre-built binaries are currently Windows-only. Linux and macOS users: see the "Install from source" section below, or the "Building a standalone executable" section further down if you want to build your own binary.

### Install from source

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

## Building a standalone executable

Users who prefer to build their own binary — for security reasons, for platforms without a pre-built release, or for learning — can produce a self-contained executable using [PyInstaller](https://pyinstaller.org/).

The maintainer builds and tests on Windows only. Linux and macOS commands are provided as reference; contributions verifying them are welcome.

### Recommended: use the spec file

The repository includes an `ascii-tree-tool.spec` file that configures PyInstaller with the correct entry point, icon, hidden imports, and windowed-mode flags. This is the maintained build path.

From the repository root:

```bash
pip install -e ".[build]"
pyinstaller ascii-tree-tool.spec
```

The built executable appears in `dist/ascii-tree-tool` (Windows: `ascii-tree-tool.exe`).

The `--clean` flag forces a fresh build against current source, wiping PyInstaller's cache:

```bash
pyinstaller --clean ascii-tree-tool.spec
```

Use `--clean` when bumping versions or after significant source changes.

<details>
<summary><strong>Manual build commands (reference)</strong></summary>

The commands below reproduce (approximately) what the spec file does, expressed as raw PyInstaller CLI flags. **The spec file above is the maintained path** — these manual commands are provided for learning and reference. They will not stay in sync with the spec file automatically; if the spec adds hidden imports or data files, this section may drift.

#### Windows

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --name ascii-tree-tool ^
  --icon assets/ASCII_Tree_Icon.ico ^
  --add-data "assets/ASCII_Tree_Icon.ico;assets" ^
  --hidden-import PyQt6.sip ^
  --paths src ^
  run_gui.py
```

#### Linux

```bash
pyinstaller \
  --onefile \
  --windowed \
  --name ascii-tree-tool \
  --add-data "assets/ASCII_Tree_Icon.ico:assets" \
  --hidden-import PyQt6.sip \
  --paths src \
  run_gui.py
```

Note: Linux PyInstaller binaries don't support icon embedding directly. Desktop icon integration (via `.desktop` files and hicolor theme directories) is out of scope.

#### macOS

```bash
pyinstaller \
  --onefile \
  --windowed \
  --name ascii-tree-tool \
  --add-data "assets/ASCII_Tree_Icon.ico:assets" \
  --hidden-import PyQt6.sip \
  --paths src \
  run_gui.py
```

Note: macOS convention embeds icons from `.icns` files rather than `.ico`. The repository does not currently include an `.icns` file (no macOS testing available). A contributor with macOS access could generate one from the source PNGs in `assets/` and add `--icon assets/ASCII_Tree_Icon.icns` above.

#### What each flag does

| Flag | Purpose |
|------|---------|
| `--onefile` | Bundle everything into a single self-extracting executable (as opposed to `--onedir`, which produces a folder of DLLs and support files alongside the .exe). |
| `--windowed` | Suppress the console window on Windows/macOS. Required for GUI apps to launch cleanly without a black cmd window appearing behind them. Alias: `--noconsole`. |
| `--name <name>` | Sets the output executable name. Without this, the .exe is named after the entry script (`run_gui.exe`). |
| `--icon <path>` | Embeds an icon into the executable's file header (Windows: `.ico`, macOS: `.icns`, Linux: not supported). |
| `--add-data "<src>;<dest>"` | Bundles a data file into the .exe. The separator is `;` on Windows and `:` on Linux/macOS. `<dest>` is the path inside the bundle where the file will be extracted at runtime. |
| `--hidden-import <module>` | Forces inclusion of a module that PyInstaller's static analysis misses. `PyQt6.sip` is the classic case — loaded dynamically via C extension mechanisms. |
| `--paths <dir>` | Adds a directory to the import search path during analysis. Needed here because the package lives under `src/` per PEP-recommended layout. |

</details>

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