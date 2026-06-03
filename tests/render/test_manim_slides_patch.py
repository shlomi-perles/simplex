"""manim-slides compatibility patch installation."""

import sys
import types

import pytest

from simplex.render import _manim_slides_patch


def _fake_manim_slides_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[types.ModuleType, object]:
    package = types.ModuleType("manim_slides")
    utils = types.ModuleType("manim_slides.utils")
    slide_package = types.ModuleType("manim_slides.slide")
    base = types.ModuleType("manim_slides.slide.base")

    def original_concatenate(_files: object, _dest: object) -> None:
        raise AssertionError("not called")

    utils.__dict__["concatenate_video_files"] = original_concatenate
    utils.__dict__["AV_VERSION_14"] = True
    utils.__dict__["logger"] = object()
    base.__dict__["concatenate_video_files"] = original_concatenate
    package.__dict__["utils"] = utils
    slide_package.__dict__["base"] = base

    monkeypatch.setitem(sys.modules, "manim_slides", package)
    monkeypatch.setitem(sys.modules, "manim_slides.utils", utils)
    monkeypatch.setitem(sys.modules, "manim_slides.slide", slide_package)
    monkeypatch.setitem(sys.modules, "manim_slides.slide.base", base)
    return utils, original_concatenate


def test_install_patches_utils_and_imported_base(monkeypatch: pytest.MonkeyPatch) -> None:
    utils, original_concatenate = _fake_manim_slides_modules(monkeypatch)
    base = sys.modules["manim_slides.slide.base"]

    assert _manim_slides_patch.install() is True

    patched = utils.__dict__["concatenate_video_files"]
    assert patched is not original_concatenate
    assert patched.__dict__["_simplex_monotonic_dts"] is True
    assert base.__dict__["concatenate_video_files"] is patched


def test_install_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    utils, _original_concatenate = _fake_manim_slides_modules(monkeypatch)

    assert _manim_slides_patch.install() is True
    patched = utils.__dict__["concatenate_video_files"]

    assert _manim_slides_patch.install() is True
    assert utils.__dict__["concatenate_video_files"] is patched
