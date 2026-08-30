"""Foundation smoke test: the project package is importable.

This is not an application or benchmark test. Optimization behavior
is not implemented and is not asserted here.
"""

from agentic_cicd import __version__


def test_package_version_is_defined() -> None:
    assert isinstance(__version__, str)
    assert __version__ != ""
