"""Tests for the release metadata and the way it reaches an installed package.

The version is declared once, in ``hammurabi/__init__.py``; ``pyproject.toml``
reads it from there, so a released wheel, ``hammurabi --version`` and the package
itself cannot disagree. A plain checkout has no installed metadata, so the tests
that need it skip instead of failing.
"""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import pytest

from hammurabi import __version__

try:  # Python 3.11 and newer; the package itself also supports 3.10.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - only Python 3.10 takes this path
    tomllib = None  # type: ignore[assignment]

#: ``pyproject.toml`` at the root of the checkout: ``tests/`` -> project root.
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

#: ``hammurabi/__init__.py``, the single source of the version.
INIT = Path(__file__).resolve().parents[1] / "src" / "hammurabi" / "__init__.py"


def _installed_metadata() -> metadata.PackageMetadata:
    """Return the installed distribution's metadata, skipping if there is none."""
    try:
        return metadata.metadata("hammurabi")
    except metadata.PackageNotFoundError:
        pytest.skip("hammurabi is not installed in this environment")


def _pyproject() -> dict:
    """Return the parsed ``pyproject.toml``, skipping on Python 3.10."""
    if tomllib is None:  # pragma: no cover - only Python 3.10 takes this path
        pytest.skip("reading pyproject.toml needs tomllib (Python 3.11+)")
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_the_installed_release_reports_the_package_version() -> None:
    assert _installed_metadata()["Version"] == __version__


def test_the_console_script_points_at_the_entry_point() -> None:
    _installed_metadata()  # skip when the package is not installed
    scripts = {
        entry.name: entry.value
        for entry in metadata.entry_points(group="console_scripts")
    }

    assert scripts["hammurabi"] == "hammurabi.main:main"


def test_pyproject_declares_the_release_metadata() -> None:
    project = _pyproject()["project"]

    assert project["readme"] == "README.md"
    assert project["description"]
    assert project["keywords"]
    assert project["classifiers"], "a release needs classifiers for the index"
    assert project["dependencies"] == ["rich>=13.0.0"]
    assert "pytest" in " ".join(project["optional-dependencies"]["dev"])


def test_pyproject_names_the_maintainer_and_the_repository() -> None:
    project = _pyproject()["project"]

    assert project["authors"] == [
        {"name": "kilofkilofa", "email": "kilofkilofa@interia.pl"}
    ]
    # These follow the published repository, so they have to point at GitHub.
    for key in ("Homepage", "Repository", "Issues"):
        assert project["urls"][key].startswith("https://github.com/")


def test_the_licence_is_declared_and_shipped() -> None:
    project = _pyproject()["project"]
    licence = PYPROJECT.parent.joinpath("LICENSE").read_text(encoding="utf-8")

    # PolyForm has no SPDX identifier, so the licence travels as a LicenseRef and
    # the full text has to ship with the package.
    assert "PolyForm" in project["license"]
    assert project["license-files"] == ["LICENSE"]
    assert licence.startswith("# PolyForm Noncommercial License 1.0.0")


def test_the_version_has_a_single_source() -> None:
    document = _pyproject()

    # No literal version in the metadata: it is read from the package instead.
    assert "version" not in document["project"]
    assert document["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "hammurabi.__version__"
    }
    assert f'__version__ = "{__version__}"' in INIT.read_text(encoding="utf-8")
