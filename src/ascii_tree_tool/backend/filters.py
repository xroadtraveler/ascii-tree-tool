# [10000] Beacon: filter predicates for the tree walker

"""Filter predicates for the tree walker.

The walker's filter_fn contract: Callable[[Path], bool], returning True to
include an entry, False to exclude. This module provides:

- Primitive builders (exclude_name, exclude_names) for constructing filters.
- A composition helper (combine_filters) for ANDing multiple filters together.
- The three Phase 1 hardcoded exclusion filters (.git/, __pycache__/, and .venv/).
- The composed Phase 1 default (default_phase1_filter).

Phase 2 will add preset filters (Python, Node, Rust, Go), .gitignore parsing,
and custom glob patterns alongside these. The primitive builders and
combine_filters helper are designed to be reused by those additions.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

# Type alias for filter predicates. Documented here so additions can reference it.
FilterFn = Callable[[Path], bool]


# [100] Subsystem: primitive filter builders

# [010] build a filter that excludes one exact name
# [SCOPE] returns a predicate callable that excludes paths whose basename matches the given name exactly (case-sensitive). Pure factory; no filesystem access.
# [OUT-OF-SCOPE] filesystem reads, glob/regex matching, case-insensitive matching

def exclude_name(name: str) -> FilterFn:
    """Return a filter predicate that excludes any path with the given basename.

    Args:
        name: Exact basename to exclude (case-sensitive). For example, ".git"
            excludes any entry literally named ".git" regardless of where it
            appears in the tree.

    Returns:
        A FilterFn that returns False for matching paths, True otherwise.
    """

    # [001] build and return predicate closure
    def predicate(path: Path) -> bool:
        return path.name != name
    return predicate
    # [-----END [001]-----]

# [-----END [010]-----]


# [020] build a filter that excludes any of a set of names
# [SCOPE] returns a predicate callable that excludes paths whose basename matches any name in the provided set (case-sensitive). Pure factory; no filesystem access.
# [OUT-OF-SCOPE] filesystem reads, glob/regex matching, case-insensitive matching

def exclude_names(names: set[str]) -> FilterFn:
    """Return a filter predicate that excludes any path whose basename is in names.

    More efficient than chaining multiple exclude_name calls when excluding
    several names at once, because the lookup is O(1) set membership.

    Args:
        names: Set of exact basenames to exclude (case-sensitive).

    Returns:
        A FilterFn that returns False for matching paths, True otherwise.
    """

    # [001] copy the set to insulate the closure from caller mutation
    excluded = set(names)
    # [-----END [001]-----]

    # [002] build and return predicate closure
    def predicate(path: Path) -> bool:
        return path.name not in excluded
    return predicate
    # [-----END [002]-----]

# [-----END [020]-----]

# [-----END [100]-----]


# [200] Subsystem: filter composition

# [010] AND-combine multiple filter predicates into one
# [SCOPE] returns a predicate callable that returns True only if every input filter returns True for the given path. Pure factory; no filesystem access.
# [OUT-OF-SCOPE] filesystem reads, OR composition, short-circuit ordering guarantees beyond left-to-right

def combine_filters(*filters: FilterFn) -> FilterFn:
    """Combine multiple filter predicates with logical AND.

    A path is included only if every filter returns True for it. Filters are
    evaluated left-to-right and short-circuit on the first False.

    Args:
        *filters: Zero or more FilterFn predicates. If zero are passed, the
            returned predicate accepts everything.

    Returns:
        A FilterFn that ANDs all the input filters.
    """

    # [001] handle empty case explicitly
    if not filters:
        return lambda _path: True
    # [-----END [001]-----]

    # [002] build and return composed predicate
    filters_tuple = tuple(filters)

    def predicate(path: Path) -> bool:
        for f in filters_tuple:
            if not f(path):
                return False
        return True
    return predicate
    # [-----END [002]-----]

# [-----END [010]-----]

# [-----END [200]-----]


# [300] Subsystem: Phase 1 hardcoded filters

# Pre-built Phase 1 filter predicates. Built once at module load and reused.
# These are the three exclusions the Phase 1 filter panel exposes as default-on
# checkboxes. The frontend reads these to populate its initial state. Users can
# uncheck any of them to include the corresponding entries in the tree output
# (e.g., for teaching, debugging, or auditing purposes).

exclude_git: FilterFn = exclude_name(".git")
"""Excludes any entry literally named '.git' (the Git metadata directory)."""

exclude_pycache: FilterFn = exclude_name("__pycache__")
"""Excludes any entry literally named '__pycache__' (Python bytecode cache)."""

exclude_venv: FilterFn = exclude_name(".venv")
"""Excludes any entry literally named '.venv' (Python virtual environment directory)."""


# [010] build the composed Phase 1 default filter
# [SCOPE] returns the composed Phase 1 default filter (excludes .git/ and __pycache__/). Pure factory; no filesystem access.
# [OUT-OF-SCOPE] filesystem reads, configuration reads, reading frontend checkbox state

def default_phase1_filter() -> FilterFn:
    """Return the composed Phase 1 default filter.

    Equivalent to combine_filters(exclude_git, exclude_pycache, exclude_venv).
    Provided as a named function so callers (smoke test, frontend default state,
    Modun embed) can request the default without duplicating the composition.

    The frontend filter panel constructs its own filter from checkbox state,
    which may include none, some, or all of these exclusions depending on what
    the user has checked. This function returns the all-defaults-on composition.

    Returns:
        A FilterFn that excludes .git/, __pycache__/, and .venv/ entries.
    """

    # [001] compose and return
    return combine_filters(exclude_git, exclude_pycache, exclude_venv)
    # [-----END [001]-----]

# [-----END [010]-----]

# [-----END [300]-----]