# [10000] Beacon: package marker for ascii_tree_tool

"""ascii-tree-tool: cross-platform desktop GUI for generating ASCII tree representations of folder structures."""

# [010] resolve installed package version

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ascii-tree-tool")
except PackageNotFoundError:
    # Package not installed via pip; running from source.
    __version__ = "0.0.0+unknown"
# [-----END [010]-----]