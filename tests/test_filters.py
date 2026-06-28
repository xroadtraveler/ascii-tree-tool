# [10000] Beacon: tests for the filter primitives, composition, and Phase 1 defaults

"""Tests for ascii_tree_tool.backend.filters.

Covers the primitive filter builders (exclude_name, exclude_names), the
composition helper (combine_filters), and the three Phase 1 pre-built
filters plus the composed default_phase1_filter.

These are pure unit tests; no filesystem fixtures are required because the
filter predicates inspect Path.name and do not perform I/O.
"""

from __future__ import annotations

from pathlib import Path

from ascii_tree_tool.backend.filters import (
    combine_filters,
    default_phase1_filter,
    exclude_git,
    exclude_name,
    exclude_names,
    exclude_pycache,
    exclude_venv,
)


# [100] Subsystem: exclude_name primitive tests

class TestExcludeName:
    """Tests for the exclude_name primitive builder."""

    # [010] test that the built predicate excludes the matching basename
    def test_excludes_matching_name(self) -> None:
        """A predicate built from exclude_name('.git') returns False for any path with that basename."""

        # [001] build and probe
        predicate = exclude_name(".git")
        assert predicate(Path(".git")) is False
        assert predicate(Path("project/.git")) is False
        assert predicate(Path("/abs/path/to/.git")) is False
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that the predicate includes non-matching basenames
    def test_includes_non_matching_names(self) -> None:
        """A predicate built from exclude_name('.git') returns True for any other basename."""

        # [001] build and probe non-matching paths
        predicate = exclude_name(".git")
        assert predicate(Path(".gitignore")) is True
        assert predicate(Path("src")) is True
        assert predicate(Path("git")) is True
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test case sensitivity
    def test_is_case_sensitive(self) -> None:
        """exclude_name matches are case-sensitive."""

        # [001] build with lowercase and probe with mixed case
        predicate = exclude_name(".git")
        assert predicate(Path(".GIT")) is True
        assert predicate(Path(".Git")) is True
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [100]-----]


# [200] Subsystem: exclude_names primitive tests

class TestExcludeNames:
    """Tests for the exclude_names primitive builder."""

    # [010] test that the predicate excludes any name in the set
    def test_excludes_any_name_in_set(self) -> None:
        """A predicate built from exclude_names returns False for any basename in the set."""

        # [001] build and probe each excluded name
        predicate = exclude_names({".git", "__pycache__", ".venv"})
        assert predicate(Path(".git")) is False
        assert predicate(Path("__pycache__")) is False
        assert predicate(Path(".venv")) is False
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that the predicate includes basenames not in the set
    def test_includes_names_not_in_set(self) -> None:
        """A predicate built from exclude_names returns True for basenames not in the set."""

        # [001] build and probe non-matching paths
        predicate = exclude_names({".git", "__pycache__"})
        assert predicate(Path("src")) is True
        assert predicate(Path("README.md")) is True
        assert predicate(Path(".gitignore")) is True
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that mutating the input set after construction does not affect the predicate
    def test_input_set_mutation_does_not_affect_predicate(self) -> None:
        """The predicate is insulated from later mutations of the input set."""

        # [001] build, mutate input, verify predicate behavior unchanged
        names = {".git"}
        predicate = exclude_names(names)
        names.add("README.md")
        assert predicate(Path("README.md")) is True
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [200]-----]


# [300] Subsystem: combine_filters composition tests

class TestCombineFilters:
    """Tests for the combine_filters composition helper."""

    # [010] test that combining filters ANDs their predicates
    def test_ands_predicates(self) -> None:
        """combine_filters returns a predicate that is True only when all inputs are True."""

        # [001] build composed filter from two primitives and probe
        composed = combine_filters(exclude_name("a"), exclude_name("b"))
        assert composed(Path("a")) is False
        assert composed(Path("b")) is False
        assert composed(Path("c")) is True
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that combine_filters with no args accepts everything
    def test_empty_input_accepts_everything(self) -> None:
        """combine_filters() with no arguments returns a predicate that accepts all paths."""

        # [001] build and probe
        composed = combine_filters()
        assert composed(Path("anything")) is True
        assert composed(Path(".git")) is True
        assert composed(Path("/abs/path")) is True
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that combine_filters with a single arg passes through its semantics
    def test_single_filter_passes_through(self) -> None:
        """combine_filters with one input behaves equivalently to that input."""

        # [001] build composed and original; verify they agree
        original = exclude_name(".git")
        composed = combine_filters(original)
        for path in [Path(".git"), Path("src"), Path(".gitignore")]:
            assert composed(path) == original(path)
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [300]-----]


# [400] Subsystem: Phase 1 pre-built filters tests

class TestPhase1PrebuiltFilters:
    """Tests for the exclude_git, exclude_pycache, and exclude_venv pre-built predicates."""

    # [010] test exclude_git
    def test_exclude_git_excludes_dot_git(self) -> None:
        """exclude_git returns False for '.git' and True for other names including '.gitignore'."""

        # [001] probe matching and non-matching
        assert exclude_git(Path(".git")) is False
        assert exclude_git(Path(".gitignore")) is True
        assert exclude_git(Path("git")) is True
        assert exclude_git(Path("src")) is True
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test exclude_pycache
    def test_exclude_pycache_excludes_pycache(self) -> None:
        """exclude_pycache returns False for '__pycache__' and True for other names."""

        # [001] probe matching and non-matching
        assert exclude_pycache(Path("__pycache__")) is False
        assert exclude_pycache(Path("pycache")) is True
        assert exclude_pycache(Path("__init__.py")) is True
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test exclude_venv
    def test_exclude_venv_excludes_dot_venv(self) -> None:
        """exclude_venv returns False for '.venv' and True for other names."""

        # [001] probe matching and non-matching
        assert exclude_venv(Path(".venv")) is False
        assert exclude_venv(Path("venv")) is True
        assert exclude_venv(Path(".venvironment")) is True
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [400]-----]


# [500] Subsystem: default_phase1_filter composition tests

class TestDefaultPhase1Filter:
    """Tests for the composed default_phase1_filter() factory."""

    # [010] test that all three Phase 1 targets are excluded
    def test_excludes_all_three_targets(self) -> None:
        """default_phase1_filter excludes .git/, __pycache__/, and .venv/."""

        # [001] build composed and probe each target
        predicate = default_phase1_filter()
        assert predicate(Path(".git")) is False
        assert predicate(Path("__pycache__")) is False
        assert predicate(Path(".venv")) is False
        # [-----END [001]-----]

    # [-----END [010]-----]


    # [020] test that non-target entries are included
    def test_includes_non_target_entries(self) -> None:
        """default_phase1_filter includes all entries that are not one of the three exclusion targets."""

        # [001] build composed and probe non-targets
        predicate = default_phase1_filter()
        assert predicate(Path("src")) is True
        assert predicate(Path("README.md")) is True
        assert predicate(Path(".gitignore")) is True
        assert predicate(Path("tests")) is True
        # [-----END [001]-----]

    # [-----END [020]-----]


    # [030] test that each call returns a fresh composed predicate (no shared state)
    def test_returns_fresh_predicate_each_call(self) -> None:
        """default_phase1_filter() builds a new composed predicate on each call."""

        # [001] call twice and verify each result behaves correctly independently
        first = default_phase1_filter()
        second = default_phase1_filter()
        assert first(Path(".git")) is False
        assert second(Path(".git")) is False
        assert first(Path("src")) is True
        assert second(Path("src")) is True
        # [-----END [001]-----]

    # [-----END [030]-----]

# [-----END [500]-----]