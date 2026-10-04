"""Tests for the video compression script."""

import importlib.util
import json
import os
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

_SCRIPT = f"{os.path.dirname(__file__)}/../scripts/compress_videos.py"
_SPEC = importlib.util.spec_from_file_location("compress_videos", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
compress_videos = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(compress_videos)


@pytest.fixture(scope="module", params=["constant-rate", "variable-rate", "edited"])
def source_video(
    tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest
) -> str:
    """Return high-bitrate HEVC clips with regular, irregular or edited timelines."""
    if not all(
        shutil.which(tool)
        for tool in ("ffmpeg", "ffprobe", "MP4Box", "GetFileInfo", "SetFile")
    ):
        pytest.skip("ffmpeg, ffprobe, MP4Box, GetFileInfo and SetFile are required")
    file_path = f"{tmp_path_factory.mktemp('source')}/clip.mp4"
    video_filter = "null"
    if request.param == "variable-rate":
        video_filter = "settb=1/90000,setpts=PTS+mod(N\\,3)*37"
    elif request.param == "edited":
        video_filter = "settb=1/90000,setpts=if(lt(N\\,15)\\,N/(15*TB)\\,(1+(N-15)/30)/TB)"
    subprocess.run(
        [
            *("ffmpeg", "-v", "error", "-f", "lavfi"),
            *("-i", "testsrc2=size=640x360:rate=30:duration=1"),
            *("-vf", video_filter),
            *("-c:v", "hevc_videotoolbox", "-b:v", "20M", "-tag:v", "hvc1"),
            *("-fps_mode", "passthrough", "-enc_time_base:v", "1/90000"),
            *("-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709"),
            *("-color_trc", "bt709", "-color_primaries", "bt709", file_path),
        ],
        check=True,
    )
    if request.param == "edited":
        subprocess.run(
            [compress_videos.require_tool("MP4Box"), "-edits", "1=re0-0.5,1", file_path],
            check=True,
        )
    return file_path


@pytest.mark.parametrize("use_outdir", [True, False], ids=["outdir", "suffix"])
@pytest.mark.parametrize("expect_compressed", [True, False], ids=["accepted", "rejected"])
def test_min_reduction(
    source_video: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    use_outdir: bool,
    expect_compressed: bool,
) -> None:
    """Keep originals, clean temporary files and map only published outputs."""
    if not expect_compressed:
        monkeypatch.setattr(compress_videos, "MIN_SIZE_REDUCTION", 0.999)
    source_path = f"{tmp_path}/clip.mp4"
    shutil.copy2(source_video, source_path)
    outdir = f"{tmp_path}/out" if use_outdir else None
    suffix = "-small"
    out_path = compress_videos.output_path(source_path, outdir, suffix)
    monkeypatch.chdir(tmp_path)

    exit_code = compress_videos.main([source_path], outdir, suffix, write_file_map=True)

    expect_output = expect_compressed or use_outdir
    assert exit_code == 0
    assert os.path.isfile(out_path) == expect_output
    assert not any(name.startswith(".") for name in os.listdir(os.path.dirname(out_path)))
    with open(f"{outdir or tmp_path}/file_map.json", encoding="utf-8") as map_file:
        assert json.load(map_file) == ({source_path: out_path} if expect_output else {})
    if not expect_output:
        return
    with open(source_path, "rb") as source_file, open(out_path, "rb") as output_file:
        is_copy = source_file.read() == output_file.read()
    assert is_copy != expect_compressed
    assert os.stat(out_path).st_mtime_ns == os.stat(source_path).st_mtime_ns
    if expect_compressed:
        assert os.path.getsize(out_path) <= (
            1 - compress_videos.MIN_SIZE_REDUCTION
        ) * os.path.getsize(source_path)
        frame_times: list[list[Fraction]] = []
        ffprobe = compress_videos.require_tool("ffprobe")
        for file_path in (source_path, out_path):
            probe = json.loads(
                subprocess.check_output(
                    [
                        ffprobe,
                        "-v",
                        "error",
                        "-select_streams",
                        "v:0",
                        "-show_frames",
                        "-show_streams",
                        "-of",
                        "json",
                        file_path,
                    ],
                    text=True,
                )
            )
            time_base = Fraction(probe["streams"][0]["time_base"])
            frame_times.append([frame["pts"] * time_base for frame in probe["frames"]])
        assert frame_times[0] == frame_times[1]


@pytest.mark.parametrize("source_video", ["variable-rate"], indirect=True)
def test_changed_timestamps_are_rejected(
    source_video: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An encoder clock that rounds frame timestamps is rejected before publication."""
    run_command = compress_videos.run_command

    def run_with_wrong_clock(command: list[str], *, capture_output: bool = False) -> str:
        """Force the nominal frame clock to reproduce encoder timestamp rounding."""
        if "-enc_time_base:v" in command:
            command = command.copy()
            command[command.index("-enc_time_base:v") + 1] = "1/30"
        return run_command(command, capture_output=capture_output)

    monkeypatch.setattr(compress_videos, "run_command", run_with_wrong_clock)
    with pytest.raises(RuntimeError, match="Video presentation timestamps changed"):
        compress_videos.main([source_video], str(tmp_path))
    assert not os.listdir(tmp_path)


@pytest.mark.parametrize("missing_tool", ["GetFileInfo", "SetFile", "MP4Box"])
def test_missing_tool_fails_before_encoding(
    missing_tool: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing tool aborts upfront instead of silently skipping metadata restoration."""
    monkeypatch.setattr(
        compress_videos.shutil, "which", lambda name: None if name == missing_tool else name
    )
    monkeypatch.setattr(compress_videos, "compress_video", pytest.fail)
    with pytest.raises(RuntimeError, match=f"'{missing_tool}' was not found"):
        compress_videos.main(["video.mp4"])
