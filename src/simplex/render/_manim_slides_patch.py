"""Make manim-slides' video concatenation deterministic.

manim-slides assembles each slide by stream-copying its partial-movie packets
through PyAV's MP4 muxer (``manim_slides.utils.concatenate_video_files``). At a
clip boundary the concat demuxer can hand the muxer a packet whose DTS is not
strictly greater than the previous one; the MP4 muxer then rejects it with a
generic ``AVERROR(EINVAL)`` surfaced as ``Invalid argument ... returned 22``.
The failure is non-deterministic and can hit a different slide on every run
(jeertmans/manim-slides#390, #540), so retrying the whole render does not
reliably clear it.

We replace the function with an identical stream-copy that nudges any
non-monotonic DTS to ``prev + 1`` (shifting PTS by the same amount to preserve
``pts >= dts``). The perturbation is at most a few stream-timebase ticks --
imperceptible -- and makes concatenation succeed deterministically without
re-encoding or an external ffmpeg binary.

Installed from :func:`simplex.plugin.activate`, which runs once per render
process before any slide is saved. Idempotent and defensive: if the manim-slides
internals it targets ever change shape, installation is skipped and the original
(occasionally-flaky) implementation is left in place.
"""

from __future__ import annotations

import importlib
import shutil
import tempfile
from pathlib import Path

_PATCH_FLAG = "_simplex_monotonic_dts"


def _make_safe_concatenate(av, av_version_14, logger):  # type: ignore[no-untyped-def]
    def concatenate_video_files(files, dest) -> None:  # type: ignore[no-untyped-def]
        """Concatenate video files, enforcing strictly monotonic DTS."""
        files = list(files)
        if len(files) == 1:
            shutil.copy(files[0], dest)
            return

        def _filter(files):  # type: ignore[no-untyped-def]
            for file in files:
                with av.open(str(file)) as container:
                    if len(container.streams.video) > 0:
                        yield file
                    else:
                        logger.warning(
                            f"Skipping video file {file} because it does "
                            "not contain any video stream. "
                            "This is probably caused by Manim, see: "
                            "https://github.com/jeertmans/manim-slides/issues/390."
                        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            # Forward slashes avoid the concat demuxer treating Windows
            # backslashes as escape characters.
            f.writelines(f"file '{Path(file).resolve().as_posix()}'\n" for file in _filter(files))
            tmp_file = f.name

        try:
            with (
                av.open(tmp_file, format="concat", options={"safe": "0"}) as input_container,
                av.open(str(dest), mode="w") as output_container,
            ):
                input_video_stream = input_container.streams.video[0]
                output_video_stream = (
                    output_container.add_stream_from_template(input_video_stream)
                    if av_version_14
                    else output_container.add_stream(template=input_video_stream)
                )

                output_audio_stream = None
                if len(input_container.streams.audio) > 0:
                    input_audio_stream = input_container.streams.audio[0]
                    output_audio_stream = (
                        output_container.add_stream_from_template(input_audio_stream)
                        if av_version_14
                        else output_container.add_stream(template=input_audio_stream)
                    )

                last_dts: dict[object, int] = {}
                for packet in input_container.demux():
                    if packet.dts is None:
                        continue

                    ptype = packet.stream.type
                    if ptype == "video":
                        packet.stream = output_video_stream
                    elif ptype == "audio":
                        if output_audio_stream is None:
                            continue
                        packet.stream = output_audio_stream
                    else:
                        continue  # We don't support subtitles

                    prev = last_dts.get(packet.stream)
                    if prev is not None and packet.dts <= prev:
                        shift = prev + 1 - packet.dts
                        packet.dts += shift
                        if packet.pts is not None:
                            packet.pts += shift
                    last_dts[packet.stream] = packet.dts

                    output_container.mux(packet)
        finally:
            Path(tmp_file).unlink()

    return concatenate_video_files


def install() -> bool:
    """Install the monotonic-DTS concat into manim-slides. Returns success.

    No-op (returns ``True``) if already installed; returns ``False`` and leaves
    the originals untouched if manim-slides isn't importable or its internals
    don't match what we expect.
    """
    try:
        import av
        from manim_slides import utils as ms_utils
    except Exception:
        return False

    if getattr(ms_utils.concatenate_video_files, _PATCH_FLAG, False):
        return True

    av_version_14 = getattr(ms_utils, "AV_VERSION_14", None)
    logger = getattr(ms_utils, "logger", None)
    if av_version_14 is None or logger is None:
        return False

    patched = _make_safe_concatenate(av, av_version_14, logger)
    setattr(patched, _PATCH_FLAG, True)

    # utils.reverse_video_file calls utils.concatenate_video_files internally,
    # so patching the utils module covers the reverse path. base.py binds its
    # own reference at import time, so patch it too if it's already imported.
    ms_utils.concatenate_video_files = patched
    try:
        ms_base = importlib.import_module("manim_slides.slide.base")
        ms_base.__dict__["concatenate_video_files"] = patched
    except Exception:
        return True
    return True
