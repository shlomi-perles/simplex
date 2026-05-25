"""Slide base class, outline scene, and chrome factory.

Re-usable mobjects live in :mod:`simplex.mobjects`; the slide hierarchy
enum lives in :mod:`simplex.section`; the deck manifest schema lives in
:mod:`simplex.manifest`.
"""

from simplex.slides.base import BaseSlide
from simplex.slides.chrome import Chrome, make_chrome
from simplex.slides.outline import OutlinePart, OutlineScene

__all__ = ["BaseSlide", "Chrome", "OutlinePart", "OutlineScene", "make_chrome"]
