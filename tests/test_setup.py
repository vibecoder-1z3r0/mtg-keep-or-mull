"""Test that the test framework is set up correctly."""

import mtg_keep_or_mull


def test_package_version() -> None:
    """Verify package version is defined."""
    assert hasattr(mtg_keep_or_mull, "__version__")
    assert mtg_keep_or_mull.__version__ == "0.1.0"


def test_package_metadata() -> None:
    """Verify package metadata is defined."""
    assert hasattr(mtg_keep_or_mull, "__author__")
    assert hasattr(mtg_keep_or_mull, "__license__")


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0
