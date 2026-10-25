"""Tests for the video compression script."""

import json
import os
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import compress_videos
import pytest


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
            # a camera's encoder tag: ffmpeg's own would mark the clip as already compressed
            *("-metadata:s:v:0", "encoder=HEVC Coding"),
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
        compress_videos.main([source_video], str(tmp_path), quality=40)
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


def test_on_error_print_continues_and_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """on_error='print' reports every failure, keeps going and still exits non-zero."""
    monkeypatch.setattr(compress_videos.shutil, "which", lambda name: name)

    def fail(input_file: str, *_args: object, **_kwargs: object) -> None:
        raise RuntimeError(f"broken {input_file}")

    monkeypatch.setattr(compress_videos, "compress_video", fail)
    assert compress_videos.main(["a.mp4", "b.mp4"], on_error="print") == 1
    assert capsys.readouterr().err.splitlines() == [
        "a.mp4: broken a.mp4",
        "b.mp4: broken b.mp4",
    ]


@pytest.mark.parametrize(
    ("unreadable", "skipped"),
    [
        ("com.apple.security.private.scoped-bookmark-token", True),
        ("com.example.ordinary", False),
    ],
)
def test_copy_macos_metadata_skips_only_protected_xattrs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    unreadable: str,
    *,
    skipped: bool,
) -> None:
    """Unreadable macOS sandbox xattrs are skipped with a warning; other failures raise."""
    source, target = tmp_path / "in.mp4", tmp_path / "out.mp4"
    source.write_bytes(b"source")
    target.write_bytes(b"target")
    monkeypatch.setattr(
        compress_videos, "xattr_names", lambda _path: ["com.apple.provenance", unreadable]
    )
    written: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> str:
        if command[:2] == ["xattr", "-px"]:
            if command[2] == unreadable:
                raise RuntimeError(f"Command failed (1): xattr -px {unreadable}")
            return "00 01"
        if command[:2] == ["xattr", "-wx"]:
            written.append(command[2])
        return ""

    monkeypatch.setattr(compress_videos, "run_command", fake_run)
    if not skipped:
        with pytest.raises(RuntimeError, match=unreadable):
            compress_videos.copy_macos_metadata(str(source), str(target))
        return
    compress_videos.copy_macos_metadata(str(source), str(target))
    assert written == ["com.apple.provenance"]
    assert f"Skipping unreadable protected attribute {unreadable}" in capsys.readouterr().out


def test_xattr_names_lists_attributes(tmp_path: Path) -> None:
    """xattr_names returns attribute names set on a file."""
    file_path = tmp_path / "file"
    file_path.write_bytes(b"")
    subprocess.run(
        ["/usr/bin/xattr", "-w", "com.example.test", "value", file_path], check=True
    )
    assert "com.example.test" in compress_videos.xattr_names(str(file_path))


DOLBY_VISION = {
    "side_data_type": "DOVI configuration record",
    "dv_profile": 8,
    "dv_level": 7,
    "rpu_present_flag": 1,
    "el_present_flag": 0,
    "bl_present_flag": 1,
    "dv_bl_signal_compatibility_id": 4,
}


@pytest.mark.parametrize(
    ("stream", "reason"),
    [
        ({"tags": {"encoder": "HEVC Coding"}}, None),
        ({"tags": {"encoder": "Lavc62.28.102 hevc_videotoolbox"}}, "already compressed"),
        ({"tags": {"encoder": "Lavc62.28.102 libx265"}}, "already compressed"),
        ({"side_data_list": [{"side_data_type": "Stereo 3D"}]}, "spatial"),
        ({"side_data_list": [DOLBY_VISION]}, None),
        (
            {"side_data_list": [DOLBY_VISION | {"el_present_flag": 1}]},
            "dual-layer Dolby Vision",
        ),
    ],
)
def test_skip_reason(stream: dict, reason: str | None) -> None:
    """Already compressed, spatial and dual-layer Dolby Vision videos are not re-encoded."""
    found = compress_videos.skip_reason(stream)
    assert (found is None) if reason is None else (reason in str(found))


@pytest.mark.parametrize("source_video", ["constant-rate"], indirect=True)
def test_compressed_output_is_skipped(source_video: str, tmp_path: Path) -> None:
    """Running again on a compressed output skips it rather than re-encoding it."""
    first, second = f"{tmp_path}/first", f"{tmp_path}/second"
    assert compress_videos.main([source_video], first) == 0
    compressed = f"{first}/clip.mp4"
    assert compress_videos.main([compressed], second) == 0
    with open(compressed, "rb") as source, open(f"{second}/clip.mp4", "rb") as copy:
        assert source.read() == copy.read()


@pytest.mark.parametrize("source_video", ["constant-rate"], indirect=True)
def test_rotated_video_vmaf_search(source_video: str, tmp_path: Path) -> None:
    """Portrait (display-rotated) clips are scored unrotated and keep their rotation."""
    rotated = f"{tmp_path}/rotated.mp4"
    subprocess.run(
        [
            *("ffmpeg", "-v", "error", "-display_rotation", "90", "-i", source_video),
            *("-map", "0", "-c", "copy", rotated),
        ],
        check=True,
    )
    assert compress_videos.main([rotated], f"{tmp_path}/out") == 0
    for path in (rotated, f"{tmp_path}/out/rotated.mp4"):
        stream = compress_videos.probe_video("ffprobe", path)["streams"][0]
        assert compress_videos.display_matrix(stream) is not None


@pytest.mark.parametrize(
    ("source_side_data", "output_side_data", "error"),
    [
        (
            [DOLBY_VISION],
            [DOLBY_VISION | {"side_data_type": "DOVI configuration record"}],
            None,
        ),
        ([DOLBY_VISION], [], "DOVI configuration record changed"),
        (
            [{"side_data_type": "Mastering display metadata", "max_luminance": "1000/1"}],
            [],
            "Mastering display",
        ),
        (
            [],
            [{"side_data_type": "Content light level metadata", "max_content": 1000}],
            "Content light level",
        ),
    ],
)
def test_verify_output_checks_hdr_side_data(
    source_side_data: list, output_side_data: list, error: str | None
) -> None:
    """Lost or altered HDR metadata (Dolby Vision, mastering, light level) is rejected."""
    stream = {
        "codec_type": "video",
        "codec_name": "hevc",
        "codec_tag_string": "hvc1",
        "id": "0x1",
    }
    stream |= {"avg_frame_rate": "30/1", "pix_fmt": "yuv420p"}
    source = {
        "streams": [stream | {"side_data_list": source_side_data}],
        "format": {"duration": "1"},
    }
    output = {
        "streams": [stream | {"side_data_list": output_side_data}],
        "format": {"duration": "1"},
    }
    if error is None:
        compress_videos.verify_output(source, output, 0)
        return
    with pytest.raises(RuntimeError, match=error):
        compress_videos.verify_output(source, output, 0)


@pytest.mark.parametrize(
    ("source_pix_fmt", "output_pix_fmt", "ten_bit", "error"),
    [
        ("yuv420p", "yuv420p10le", True, None),
        ("yuv420p", "yuv420p", False, None),
        ("yuv420p10le", "yuv420p10le", True, None),
        ("yuv420p10le", "yuv420p10le", False, None),
        ("yuv420p", "yuv420p", True, "pix_fmt"),
        ("yuv420p", "yuv420p10le", False, "pix_fmt"),
        ("yuv420p10le", "yuv420p", False, "pix_fmt"),
    ],
)
def test_verify_output_pixel_format(
    source_pix_fmt: str, output_pix_fmt: str, *, ten_bit: bool, error: str | None
) -> None:
    """Only ten_bit may lift 8-bit to 10-bit; any other pixel format change is rejected."""
    stream = {"codec_type": "video", "codec_name": "hevc", "codec_tag_string": "hvc1"}
    stream |= {"id": "0x1", "avg_frame_rate": "30/1"}
    source = {"streams": [stream | {"pix_fmt": source_pix_fmt}], "format": {"duration": "1"}}
    output = {"streams": [stream | {"pix_fmt": output_pix_fmt}], "format": {"duration": "1"}}
    if error is None:
        compress_videos.verify_output(source, output, 0, ten_bit=ten_bit)
        return
    with pytest.raises(RuntimeError, match=error):
        compress_videos.verify_output(source, output, 0, ten_bit=ten_bit)


def test_dolby_vision_config_is_restored_on_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """The re-encoded track gets the source's Dolby Vision profile and compatibility ID."""
    commands: list[list[str]] = []
    monkeypatch.setattr(
        compress_videos, "run_command", lambda command, **_: commands.append(command) or ""
    )
    probe = {"streams": [{"id": "0x1", "side_data_list": [DOLBY_VISION]}]}
    compress_videos.replace_video_track(
        "MP4Box", "in.mov", "enc.mp4", "out.mov", source_probe=probe, stream_position=0
    )
    assert commands[0][2] == "enc.mp4#trackID=1:ID=2:tkidx=1:dvp=8.4"


@pytest.mark.parametrize("source_video", ["constant-rate"], indirect=True)
def test_parallel_jobs_keep_file_map_order(
    source_video: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Concurrent jobs compress every file and write the file map in input order."""
    sources = []
    for name in ("b", "a", "c"):
        sources.append(f"{tmp_path}/{name}.mp4")
        shutil.copy2(source_video, sources[-1])
    outdir = f"{tmp_path}/out"
    monkeypatch.chdir(tmp_path)
    assert compress_videos.main(sources, outdir, write_file_map=True, jobs=2) == 0
    with open(f"{outdir}/file_map.json", encoding="utf-8") as map_file:
        assert list(json.load(map_file)) == sources


@pytest.mark.parametrize("source_video", ["constant-rate"], indirect=True)
@pytest.mark.parametrize(
    ("encoder", "quality", "ten_bit", "pix_fmt"),
    [
        ("videotoolbox", 40, True, "yuv420p10le"),
        ("videotoolbox", 50, False, "yuv420p"),
        ("x265", 28, True, "yuv420p10le"),
    ],
)
def test_encoder_and_bit_depth(
    source_video: str,
    tmp_path: Path,
    *,
    encoder: compress_videos.Encoder,
    quality: int,
    ten_bit: bool,
    pix_fmt: str,
) -> None:
    """Both encoders publish verified HEVC; ten_bit lifts 8-bit sources to Main10."""
    exit_code = compress_videos.main(
        [source_video], str(tmp_path), quality=quality, encoder=encoder, ten_bit=ten_bit
    )
    assert exit_code == 0
    probe = compress_videos.probe_video("ffprobe", f"{tmp_path}/clip.mp4")
    assert probe["streams"][0]["pix_fmt"] == pix_fmt


def test_x265_refuses_hdr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """x265 would drop HDR side data, so HDR sources fail before encoding."""
    stream = {"codec_type": "video", "pix_fmt": "yuv420p10le", "tags": {}}
    stream["side_data_list"] = [{"side_data_type": "Mastering display metadata"}]
    monkeypatch.setattr(
        compress_videos, "probe_video", lambda *_: {"streams": [stream], "format": {}}
    )
    source = tmp_path / "in.mp4"
    source.write_bytes(b"")
    with pytest.raises(ValueError, match="x265 would drop Mastering display metadata"):
        compress_videos.compress_video(
            str(source),
            f"{tmp_path}/out.mp4",
            quality=24,
            target_vmaf=None,
            speed_priority=True,
            overwrite=False,
            keep_original=False,
            encoder="x265",
            ffmpeg="ffmpeg",
            ffprobe="ffprobe",
            mp4box="MP4Box",
        )


@pytest.mark.parametrize(
    ("encoder", "start", "threshold", "expected"),
    [
        # VideoToolbox: VMAF rises with -q:v, so pick the lowest passing q
        ("videotoolbox", 62, 57, 57),
        ("videotoolbox", 50, 57, 57),
        ("videotoolbox", 62, 95, 90),  # target unreachable: best quality in range
        # x265: VMAF falls with -crf, so pick the highest passing crf
        ("x265", 24, 27, 27),
        ("x265", 30, 21, 21),
        ("x265", 24, 10, 14),  # target unreachable: best quality in range
    ],
)
def test_choose_quality(
    monkeypatch: pytest.MonkeyPatch,
    encoder: compress_videos.Encoder,
    start: int,
    threshold: int,
    expected: int,
) -> None:
    """The search finds the smallest-file quality passing the target for both encoders."""
    encoded: list[int] = []

    def fake_encode(*_args: object, quality: int, **_kwargs: object) -> None:
        """Record the quality instead of encoding."""
        encoded.append(quality)

    def fake_vmaf(*_args: object, **_kwargs: object) -> float:
        """Pass iff the last encoded quality is at least as good as the threshold."""
        direction = compress_videos.ENCODERS[encoder][3]
        return 100.0 if direction * encoded[-1] >= direction * threshold else 0.0

    monkeypatch.setattr(compress_videos, "encode_video", fake_encode)
    monkeypatch.setattr(compress_videos, "vmaf_score", fake_vmaf)
    quality, _ = compress_videos.choose_quality(
        "ffmpeg",
        "in.mp4",
        "tmp",
        stream_position=0,
        source_stream={"width": 3840},
        windows=[(0.0, 3.0)],
        target_vmaf=50.0,
        start_quality=start,
        speed_priority=True,
        encoder=encoder,
        ten_bit=True,
    )
    assert quality == expected
