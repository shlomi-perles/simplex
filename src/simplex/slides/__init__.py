"""Slide classes, outline scene, and chrome factory.

Reusable mobjects live in :mod:`simplex.mobjects`; the slide hierarchy
enum lives in :mod:`simplex.section`; the deck manifest schema lives in
:mod:`simplex.manifest`.
"""

from simplex.slides.base import BaseSlide, SimplexScene, SimplexThreeDScene, Slide, ThreeDSlide
from simplex.slides.chrome import Chrome, make_chrome
from simplex.slides.outline import OutlinePart, OutlineScene

__all__ = [
    "BaseSlide",
    "Chrome",
    "OutlinePart",
    "OutlineScene",
    "SimplexScene",
    "SimplexThreeDScene",
    "Slide",
    "ThreeDSlide",
    "make_chrome",
]
