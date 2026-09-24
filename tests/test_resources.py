"""Resource resolution must survive freezing.

The packaged build once produced a binary that started and then could not find
its own AI verifier weights, because the lookup walked ``__file__.parents[2]``
and escaped the PyInstaller bundle. These tests pin the three cases that
matters: a source checkout, a frozen bundle, and a resource that is absent.
"""
import pathlib

import pytest

from fsoc_pat import resources


def test_source_checkout_finds_shipped_data():
    assert resources.model().exists()
    assert resources.scenarios_dir().is_dir()
    assert resources.default_scenario().exists()


def test_frozen_bundle_is_preferred(tmp_path, monkeypatch):
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "track_verifier.npz").write_bytes(b"weights")
    (tmp_path / "scenarios").mkdir()
    (tmp_path / "scenarios" / "leo_pass_nominal.yaml").write_text("name: x")

    monkeypatch.setattr(resources.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(resources.sys, "frozen", True, raising=False)

    assert resources.model() == tmp_path / "models" / "track_verifier.npz"
    assert resources.default_scenario() == tmp_path / "scenarios" / "leo_pass_nominal.yaml"
    assert resources.scenarios_dir() == tmp_path / "scenarios"


def test_missing_resource_returns_path_without_raising():
    """The verifier loader tests .exists() and degrades to classical-only."""
    ghost = resources.bundled("models", "definitely_not_here.npz")
    assert isinstance(ghost, pathlib.Path)
    assert not ghost.exists()


def test_writable_dir_is_created_and_outside_the_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("FSOC_PAT_HOME", str(tmp_path / "home"))
    target = resources.writable_dir("web")
    assert target.is_dir()
    assert str(tmp_path / "home") in str(target)
