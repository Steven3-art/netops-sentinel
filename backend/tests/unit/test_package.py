"""Tests for the NetOps Sentinel package metadata."""

import netops_sentinel


def test_package_version() -> None:
    """The package exposes the expected project version."""
    assert netops_sentinel.__version__ == "0.1.0"
