"""Compress videos to HEVC while retaining the original MP4 metadata."""

from __future__ import annotations

import concurrent.futures
import ctypes
import ctypes.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Sequence

__author__ = "Janosh Riebesell"
__date__ = "2022-07-04"

# quality: (VMAF search start, search range, search stride, direction, max). VideoToolbox
# -q:v grows with quality, x265 -crf shrinks with it. Starts are typical picks for VMAF 95.
ENCODERS = {
    "videotoolbox": (50, (30, 90), 4, 1, 100),
    "x265": (27, (14, 34), 2, -1, 51),
}
Encoder = Literal["videotoolbox", "x265"]
DEFAULT_JOBS = 1  # files encoded concurrently
DEFAULT_TARGET_VMAF = 95.0  # near-transparent on 4K drone footage
SAMPLE_SECONDS = 3.0  # length of each excerpt used to pick and check quality
VMAF_4K_WIDTH = 3000  # videos at least this wide are scored with VMAF's 4K model
VMAF_MARGIN = 1.0  # final samples may score this far below the target (encoder variance)
MIN_SIZE_REDUCTION = 0.1  # re-encodes saving less are rejected
MIN_VMAF = 90.0  # without a VMAF target, re-encodes scoring lower are rejected as broken
DISPLAY_MATRIX_VALUES = 9
_COMMON_COLOR_CODES = {
    "bt709": 1,
    "bt470bg": 5,
    "smpte170m": 6,
    "smpte240m": 7,
}
COLOR_PRIMARIES = _COMMON_COLOR_CODES | {
    "bt470m": 4,
    "bt2020": 9,
    "smpte431": 11,
    "smpte432": 12,
}
COLOR_TRANSFERS = _COMMON_COLOR_CODES | {
    "bt470m": 4,
    "iec61966-2-1": 13,
    "bt2020-10": 14,
    "bt2020-12": 15,
    "smpte2084": 16,
    "arib-std-b67": 18,
}
COLOR_MATRICES = _COMMON_COLOR_CODES | {
    "rgb": 0,
    "fcc": 4,
    "bt2020nc": 9,
    "bt2020c": 10,
}
VIDEO_PROPERTY_KEYS = (
    "width height pix_fmt color_range color_space color_transfer color_primaries".split()
)
# Encoders whose output this script produces: such files are already compressed
COMPRESSED_ENCODERS = ("hevc_videotoolbox", "libx265")
# HDR side data that must survive re-encoding unchanged
DOLBY_VISION_CONFIG = "DOVI configuration record"
DOLBY_VISION_KEYS = (
    "dv_profile dv_level rpu_present_flag el_present_flag bl_present_flag "
    "dv_bl_signal_compatibility_id".split()
)
HDR_SIDE_DATA = (
    DOLBY_VISION_CONFIG,
    "Mastering display metadata",
    "Content light level metadata",
)
DOLBY_VISION_RPU_NAL_TYPE = 62
AUXILIARY_STREAM_KEYS = (
    "id codec_type codec_name codec_tag_string duration nb_frames tags disposition".split()
)


def require_tool(name: str) -> str:
    """Return the absolute path to a required executable."""
    if path := shutil.which(name):
        return path
    raise RuntimeError(
        f"Required executable {name!r} was not found. "
        "Install with `brew install ffmpeg gpac` "
        "(GetFileInfo/SetFile: `xcode-select --install`)."
    )


def run_command(command: Sequence[str], *, capture_output: bool = False) -> str:
    """Run a command, returning stdout and including captured diagnostics in failures."""
    result = subprocess.run(
        command,
        capture_output=capture_output,
        check=False,
        text=True,
    )
    if result.returncode:
        diagnostics = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part
        )
        message = f"Command failed ({result.returncode}): {' '.join(command)}"
        raise RuntimeError(f"{message}\n{diagnostics}" if diagnostics else message)
    return result.stdout or ""


def probe_video(ffprobe: str, file_path: str) -> dict[str, Any]:
    """Return all stream and container metadata reported by FFprobe."""
    flags = "-v error -show_format -show_streams -of json".split()
    return json.loads(run_command([ffprobe, *flags, file_path], capture_output=True))


def presentation_timestamps(
    ffprobe: str, file_path: str, stream_position: int, time_base: str
) -> list[Fraction]:
    """Return exact presentation times of video packets not marked for discard."""
    flags = f"-v error -select_streams {stream_position} -show_packets "
    flags += "-show_entries packet=pts,flags -of json"
    command = [ffprobe, *flags.split(), file_path]
    packet_probe = json.loads(run_command(command, capture_output=True))
    seconds_per_tick = Fraction(time_base)
    return sorted(
        packet["pts"] * seconds_per_tick
        for packet in packet_probe["packets"]
        if "D" not in packet["flags"]
    )


def metadata_changes(
    source_tags: dict[str, Any],
    output_tags: dict[str, Any],
    *,
    ignored_keys: tuple[str, ...] = (),
) -> dict[str, tuple[Any, Any]]:
    """Return source metadata fields that changed in the output."""
    return {
        key: (value, output_tags.get(key))
        for key, value in source_tags.items()
        if key not in ignored_keys and output_tags.get(key) != value
    }


def primary_video_stream(probe: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Return the position and metadata of the first non-thumbnail video stream."""
    for position, stream in enumerate(probe["streams"]):
        is_thumbnail = stream.get("disposition", {}).get("attached_pic") == 1
        if stream.get("codec_type") == "video" and not is_thumbnail:
            return position, stream
    raise ValueError("Input has no primary video stream")


def track_id(stream: dict[str, Any]) -> int:
    """Parse an FFprobe MP4 track ID such as ``0x1``."""
    if (value := stream.get("id")) is None:
        raise ValueError("Primary video stream has no MP4 track ID")
    return int(str(value), 0)


def side_data(stream: dict[str, Any], side_data_type: str) -> dict[str, Any] | None:
    """Return a stream's side data entry of the given type, if present."""
    return next(
        (
            entry
            for entry in stream.get("side_data_list", [])
            if entry.get("side_data_type") == side_data_type
        ),
        None,
    )


def skip_reason(stream: dict[str, Any]) -> str | None:
    """Why a video must not be re-encoded, or None if it can be.

    Already compressed files would only lose quality again. The hardware encoder writes a
    single layer, so it would drop the second view of spatial (MV-HEVC) video and the
    enhancement layer of dual-layer Dolby Vision.
    """
    encoder = stream.get("tags", {}).get("encoder", "")
    if any(name in encoder for name in COMPRESSED_ENCODERS):
        return f"already compressed (encoder {encoder!r})"
    if side_data(stream, "Stereo 3D") or stream.get("view_ids_available"):
        return "spatial (MV-HEVC) video: re-encoding would drop the second view"
    dolby_vision = side_data(stream, DOLBY_VISION_CONFIG)
    if dolby_vision and dolby_vision.get("el_present_flag"):
        return "dual-layer Dolby Vision: re-encoding would drop the enhancement layer"
    return None


def dolby_vision_rpu_count(ffmpeg: str, file_path: str, stream_position: int) -> int:
    """Count Dolby Vision RPU NAL units (per-frame HDR metadata) in an HEVC stream."""
    command = [ffmpeg, "-v", "error", "-i", file_path, "-map", f"0:{stream_position}"]
    command += ["-c", "copy", "-bsf:v", "hevc_mp4toannexb", "-f", "hevc", "-"]
    stream = subprocess.run(command, capture_output=True, check=True).stdout
    count, start = 0, stream.find(b"\x00\x00\x01")
    while start != -1 and start + 3 < len(stream):
        count += (stream[start + 3] >> 1) & 0x3F == DOLBY_VISION_RPU_NAL_TYPE
        start = stream.find(b"\x00\x00\x01", start + 3)
    return count


def display_matrix(stream: dict[str, Any]) -> str | None:
    """Return a colon-separated QuickTime display matrix, if present."""
    for side_data in stream.get("side_data_list", []):
        if side_data.get("side_data_type") != "Display Matrix":
            continue
        values: list[str] = []
        for line in side_data.get("displaymatrix", "").splitlines():
            if ":" in line:
                values.extend(line.split(":", maxsplit=1)[1].split())
        if len(values) == DISPLAY_MATRIX_VALUES:
            return ":".join(values)
    return None


def encode_video(
    ffmpeg: str,
    input_file: str,
    output_file: str,
    *,
    stream_position: int,
    source_stream: dict[str, Any],
    quality: int,
    speed_priority: bool,
    encoder: Encoder = "videotoolbox",
    ten_bit: bool = True,
    window: tuple[float, float] | None = None,
    quiet: bool = False,
) -> None:
    """Encode one video stream as HEVC with Apple's media engine or x265.

    ten_bit encodes 8-bit sources as 10-bit Main10 (fewer bytes at equal quality); 10-bit
    sources always stay 10-bit. With window=(start, seconds), encode only that excerpt
    (quality sampling). Excerpts and quiet encodes print no progress.
    """
    color_metadata: list[str] = []
    color_range = source_stream.get("color_range")
    if color_range in {"tv", "pc"}:
        color_metadata.append(f"video_full_range_flag={int(color_range == 'pc')}")
    for key, option, codes in (
        ("color_primaries", "colour_primaries", COLOR_PRIMARIES),
        ("color_transfer", "transfer_characteristics", COLOR_TRANSFERS),
        ("color_space", "matrix_coefficients", COLOR_MATRICES),
    ):
        value = source_stream.get(key)
        if value in codes:
            color_metadata.append(f"{option}={codes[value]}")

    # 8-bit sources are converted to 10-bit in software: scale_vt can't output P010
    pix_fmt = encoded_pix_fmt(source_stream["pix_fmt"], ten_bit=ten_bit)
    convert_to_ten_bit = pix_fmt != source_stream["pix_fmt"]
    keep_hardware_frames = encoder == "videotoolbox" and not convert_to_ten_bit
    # Split only flag strings: file paths may contain spaces.
    decode_flags = "-hide_banner -nostdin -y -hwaccel videotoolbox -noautorotate"
    if keep_hardware_frames:
        decode_flags += " -hwaccel_output_format videotoolbox_vld"
    encode_flags = f"-map 0:{stream_position} -map_metadata 0 -fps_mode passthrough"
    if encoder == "videotoolbox":
        encode_flags += f" -c:v hevc_videotoolbox -q:v {quality} "
        encode_flags += f"-prio_speed {int(speed_priority)} -spatial_aq 1"
        if convert_to_ten_bit:
            encode_flags += " -vf format=p010le -profile:v main10"
    else:
        preset = "medium" if speed_priority else "slow"
        encode_flags += f" -c:v libx265 -crf {quality} -preset {preset}"
        encode_flags += " -x265-params log-level=error"
        encode_flags += f" -pix_fmt {pix_fmt}"
    seek = ["-ss", f"{window[0]:.3f}", "-t", f"{window[1]:.3f}"] if window else []
    command = [ffmpeg, *decode_flags.split(), *seek, "-i", input_file]
    command += encode_flags.split()
    command += ["-enc_time_base:v", source_stream["time_base"], "-tag:v", "hvc1"]
    if color_metadata:
        command.extend(("-bsf:v", f"hevc_metadata={':'.join(color_metadata)}"))
    command.append(output_file)
    run_command(command, capture_output=quiet or window is not None)


def choose_quality(
    ffmpeg: str,
    input_file: str,
    tmpdir: str,
    *,
    stream_position: int,
    source_stream: dict[str, Any],
    windows: list[tuple[float, float]],
    target_vmaf: float,
    start_quality: int,
    speed_priority: bool,
    encoder: Encoder,
    ten_bit: bool,
) -> tuple[int, float]:
    """Smallest-file quality whose worst sample reaches target_vmaf, and that score.

    Steps from start_quality by the encoder's stride until the target is bracketed, then
    bisects. Returns the best quality of the search range if even that misses the target.
    Works on level = direction * quality so higher levels always mean higher quality.
    """
    _, (range_start, range_end), stride, direction, _ = ENCODERS[encoder]
    scores: dict[int, float] = {}

    def score(level: int) -> float:
        """Worst sample VMAF at a quality level, cached."""
        quality = direction * level
        if level not in scores:
            sample_scores = []
            for idx, window in enumerate(windows):
                sample = f"{tmpdir}/sample-{quality}-{idx}.mp4"
                encode_video(
                    ffmpeg,
                    input_file,
                    sample,
                    stream_position=stream_position,
                    source_stream=source_stream,
                    quality=quality,
                    speed_priority=speed_priority,
                    encoder=encoder,
                    ten_bit=ten_bit,
                    window=window,
                )
                sample_scores.append(
                    vmaf_score(
                        ffmpeg,
                        input_file,
                        sample,
                        stream_position=stream_position,
                        window=window,
                        distorted_is_excerpt=True,
                        width=source_stream["width"],
                    )
                )
            scores[level] = min(sample_scores)
        return scores[level]

    low, high = sorted((direction * range_start, direction * range_end))
    level = min(max(direction * start_quality, low), high)
    if score(level) >= target_vmaf:  # passing: step down until failing
        passing = level
        while passing > low and score(failing := max(passing - stride, low)) >= target_vmaf:
            passing = failing
        failing = max(passing - stride, low) if passing > low else passing
    else:  # failing: step up until passing
        failing = level
        while failing < high and score(passing := min(failing + stride, high)) < target_vmaf:
            failing = passing
        passing = min(failing + stride, high)
        if score(passing) < target_vmaf:
            return direction * passing, score(passing)
    while passing - failing > 1:
        middle = (passing + failing) // 2
        if score(middle) >= target_vmaf:
            passing = middle
        else:
            failing = middle
    return direction * passing, score(passing)


def sample_windows(
    duration: float, count: int = 3, seconds: float = SAMPLE_SECONDS
) -> list[tuple[float, float]]:
    """(start, seconds) excerpts spread over a video to estimate its quality cheaply."""
    if duration <= count * seconds:
        return [(0.0, duration)]
    return [((idx + 0.5) * duration / count - seconds / 2, seconds) for idx in range(count)]


def vmaf_score(
    ffmpeg: str,
    reference_file: str,
    distorted_file: str,
    *,
    stream_position: int,
    window: tuple[float, float],
    distorted_is_excerpt: bool,
    width: int,
) -> float:
    """Mean VMAF of a window of distorted_file against the same window of reference_file.

    Uses the 4K model for 4K video, else the standard 1080p model, on every other frame.
    Hardware decoding gives identical scores about 25% faster.
    """
    # Compare stored frames: autorotation would turn only the reference of a rotated
    # video, since excerpts lack the display matrix restored later from the source
    seek = ["-hwaccel", "videotoolbox", "-noautorotate"]
    seek += ["-ss", f"{window[0]:.3f}", "-t", f"{window[1]:.3f}"]
    model = "vmaf_4k_v0.6.1" if width >= VMAF_4K_WIDTH else "vmaf_v0.6.1"
    graph = (
        "[0:v]format=yuv420p10le,setpts=PTS-STARTPTS[dist];"
        f"[1:{stream_position}]format=yuv420p10le,setpts=PTS-STARTPTS[ref];"
        f"[dist][ref]libvmaf=model=version={model}:n_subsample=2:n_threads={os.cpu_count()}"
    )
    distorted_seek = seek[:3] if distorted_is_excerpt else seek
    command = [ffmpeg, "-hide_banner", "-nostdin", *distorted_seek, "-i", distorted_file]
    command += [*seek, "-i", reference_file, "-lavfi", graph, "-f", "null", "-"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode or "VMAF score:" not in result.stderr:
        raise RuntimeError(f"VMAF failed for {distorted_file}: {result.stderr[-500:]}")
    return float(result.stderr.rsplit("VMAF score:", 1)[1].split()[0])


def replace_video_track(
    mp4box: str,
    input_file: str,
    encoded_file: str,
    output_file: str,
    *,
    source_probe: dict[str, Any],
    stream_position: int,
) -> None:
    """Replace only the primary video track, retaining every other MP4 box and track."""
    source_track_id = track_id(source_probe["streams"][stream_position])
    existing_ids = [
        track_id(stream) for stream in source_probe["streams"] if stream.get("id") is not None
    ]
    temporary_track_id = max(existing_ids, default=0) + 1
    imported_track = (
        f"{encoded_file}#trackID=1:ID={temporary_track_id}:tkidx={stream_position + 1}"
    )
    # The encoder keeps each frame's Dolby Vision RPU but not the track's configuration
    # record; without it players fall back to the HDR10/HLG base layer
    source_stream = source_probe["streams"][stream_position]
    if dolby_vision := side_data(source_stream, DOLBY_VISION_CONFIG):
        profile = dolby_vision["dv_profile"]
        compatibility = dolby_vision["dv_bl_signal_compatibility_id"]
        imported_track += f":dvp={profile}.{compatibility}"
    run_command(
        [
            mp4box,
            "-add",
            imported_track,
            "-rem",
            str(source_track_id),
            "-set-track-id",
            f"{temporary_track_id}:{source_track_id}",
            "-keep-utc",
            "-no-iod",
            "-out",
            output_file,
            input_file,
        ],
        capture_output=True,
    )
    if matrix := display_matrix(source_probe["streams"][stream_position]):
        run_command(
            [mp4box, "-mx", f"{source_track_id}={matrix}", output_file],
            capture_output=True,
        )


PROTECTED_XATTR_PREFIX = "com.apple.security.private."
XATTR_NOFOLLOW = 0x0001  # <sys/xattr.h>: list the link itself, like the stat calls below


def xattr_names(file_path: str) -> list[str]:
    """Names of a file's extended attributes, via listxattr(2).

    The `xattr` CLI reads every value while listing, so a single unreadable protected
    attribute makes it fail for the whole file.
    """
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    path = os.fsencode(file_path)
    size = libc.listxattr(path, None, 0, XATTR_NOFOLLOW)
    if size < 0:
        raise OSError(ctypes.get_errno(), f"listxattr failed for {file_path}")
    buffer = ctypes.create_string_buffer(size)
    if libc.listxattr(path, buffer, size, XATTR_NOFOLLOW) < 0:
        raise OSError(ctypes.get_errno(), f"listxattr failed for {file_path}")
    return [os.fsdecode(name) for name in buffer.raw[:size].split(b"\0") if name]


def copy_macos_metadata(input_file: str, output_file: str) -> None:
    """Copy filesystem timestamps, mode, flags, and macOS extended attributes."""
    source_stat = os.stat(input_file, follow_symlinks=False)
    shutil.copystat(input_file, output_file, follow_symlinks=False)
    os.chown(output_file, source_stat.st_uid, source_stat.st_gid, follow_symlinks=False)

    for name in xattr_names(input_file):
        try:
            hex_value = run_command(["xattr", "-px", name, input_file], capture_output=True)
        except RuntimeError:
            # macOS denies every process read access to its sandbox attributes (e.g. the
            # scoped-bookmark-token apps like Mylio add), so they can't be carried over
            if not name.startswith(PROTECTED_XATTR_PREFIX):
                raise
            print(f"Skipping unreadable protected attribute {name} of {input_file}")
            continue
        run_command(
            ["xattr", "-wx", name, "".join(hex_value.split()), output_file],
            capture_output=True,
        )

    # Extended-attribute tools can update these, so restore access/modify times next.
    atime_mtime = (source_stat.st_atime_ns, source_stat.st_mtime_ns)
    os.utime(output_file, ns=atime_mtime, follow_symlinks=False)

    # Setting an mtime older than the creation date can lower the latter on APFS.
    # Restore the original creation date only after the final os.utime call.
    creation_date = run_command(["GetFileInfo", "-d", input_file], capture_output=True).strip()
    run_command(["SetFile", "-d", creation_date, output_file], capture_output=True)


def auxiliary_signatures(probe: dict[str, Any], stream_position: int) -> list[dict[str, Any]]:
    """Return stable fields of every stream except the primary video to verify them."""
    return [
        {key: stream.get(key) for key in AUXILIARY_STREAM_KEYS}
        for position, stream in enumerate(probe["streams"])
        if position != stream_position
    ]


def encoded_pix_fmt(source_pix_fmt: str, *, ten_bit: bool) -> str:
    """Pixel format the encoder writes for a source: ten_bit lifts 8-bit to 10-bit."""
    return "yuv420p10le" if ten_bit and "10" not in source_pix_fmt else source_pix_fmt


def verify_output(
    source_probe: dict[str, Any],
    output_probe: dict[str, Any],
    stream_position: int,
    *,
    ten_bit: bool = False,
) -> None:
    """Verify video properties, container tags, and all non-video streams."""
    source_video = dict(source_probe["streams"][stream_position])
    source_video["pix_fmt"] = encoded_pix_fmt(source_video["pix_fmt"], ten_bit=ten_bit)
    output_position, output_video = primary_video_stream(output_probe)
    if output_position != stream_position:
        raise RuntimeError("Primary video stream moved to a different track position")
    if (
        output_video.get("codec_name") != "hevc"
        or output_video.get("codec_tag_string") != "hvc1"
    ):
        raise RuntimeError("Primary video stream is not Apple-compatible HEVC")
    if source_video.get("id") != output_video.get("id"):
        raise RuntimeError("Primary video track ID changed")

    for key in VIDEO_PROPERTY_KEYS:
        if source_video.get(key) != output_video.get(key):
            raise RuntimeError(
                f"Video property {key!r} changed from {source_video.get(key)!r} "
                f"to {output_video.get(key)!r}"
            )

    if display_matrix(source_video) != display_matrix(output_video):
        raise RuntimeError("Video display matrix changed")

    for side_data_type in HDR_SIDE_DATA:
        source_entry = side_data(source_video, side_data_type) or {}
        output_entry = side_data(output_video, side_data_type) or {}
        if side_data_type == DOLBY_VISION_CONFIG:
            source_entry = {key: source_entry.get(key) for key in DOLBY_VISION_KEYS}
            output_entry = {key: output_entry.get(key) for key in DOLBY_VISION_KEYS}
        if source_entry != output_entry:
            raise RuntimeError(
                f"{side_data_type} changed from {source_entry} to {output_entry}"
            )

    changed_video_tags = metadata_changes(
        source_video.get("tags", {}),
        output_video.get("tags", {}),
        ignored_keys=("encoder",),
    )
    if changed_video_tags:
        raise RuntimeError(f"Video track metadata changed: {changed_video_tags}")

    duration_tolerance = max(0.05, float(2 / Fraction(source_video["avg_frame_rate"])))
    duration_delta = abs(
        float(source_probe["format"]["duration"]) - float(output_probe["format"]["duration"])
    )
    if duration_delta > duration_tolerance:
        raise RuntimeError(
            f"Duration changed by {duration_delta:.3f}s (maximum {duration_tolerance:.3f}s)"
        )

    if auxiliary_signatures(source_probe, stream_position) != auxiliary_signatures(
        output_probe, stream_position
    ):
        raise RuntimeError("One or more auxiliary streams changed during compression")

    changed_tags = metadata_changes(
        source_probe["format"].get("tags", {}),
        output_probe["format"].get("tags", {}),
    )
    if changed_tags:
        raise RuntimeError(f"Container metadata changed: {changed_tags}")


def verify_rebuilt(
    input_file: str,
    rebuilt_file: str,
    *,
    source_probe: dict[str, Any],
    stream_position: int,
    ten_bit: bool,
    ffmpeg: str,
    ffprobe: str,
) -> None:
    """Verify a rebuilt file's streams, metadata, Dolby Vision RPUs and frame timestamps."""
    video_stream = source_probe["streams"][stream_position]
    output_probe = probe_video(ffprobe, rebuilt_file)
    verify_output(source_probe, output_probe, stream_position, ten_bit=ten_bit)
    if side_data(video_stream, DOLBY_VISION_CONFIG):
        counts = [
            dolby_vision_rpu_count(ffmpeg, path, stream_position)
            for path in (input_file, rebuilt_file)
        ]
        if counts[0] != counts[1]:
            raise RuntimeError(
                f"Dolby Vision RPUs changed from {counts[0]} to {counts[1]} frames"
            )
    source_times = presentation_timestamps(
        ffprobe, input_file, stream_position, video_stream["time_base"]
    )
    output_times = presentation_timestamps(
        ffprobe,
        rebuilt_file,
        stream_position,
        output_probe["streams"][stream_position]["time_base"],
    )
    if source_times != output_times:
        first_difference = next(
            (
                times
                for times in zip(source_times, output_times, strict=False)
                if times[0] != times[1]
            ),
            None,
        )
        raise RuntimeError(
            "Video presentation timestamps changed: "
            f"source has {len(source_times)} displayed frames, "
            f"output has {len(output_times)}, first difference={first_difference}"
        )


class SkipVideo(Exception):  # noqa: N818
    """A video that must not be re-encoded; the message says why."""


def output_path(input_file: str, outdir: str | None, suffix: str) -> str:
    """Build an output path in outdir, else next to the input with suffix before the ext."""
    if outdir:
        return f"{outdir}/{os.path.basename(input_file)}"
    stem, extension = os.path.splitext(input_file)
    return f"{stem}{suffix}{extension}"


def compress_video(
    input_file: str,
    output_file: str,
    *,
    quality: int | None,
    target_vmaf: float | None,
    speed_priority: bool,
    overwrite: bool,
    keep_original: bool,
    encoder: Encoder = "videotoolbox",
    ten_bit: bool = True,
    quiet: bool = False,
    ffmpeg: str,
    ffprobe: str,
    mp4box: str,
) -> tuple[int, int, float, bool, str]:
    """Compress one video and atomically publish the verified result.

    A result saving less than MIN_SIZE_REDUCTION is discarded unverified. With
    keep_original, a copy of the input is published in its place.

    Pass exactly one of quality (fixed) and target_vmaf (quality chosen per video from
    sampled excerpts). Accepted re-encodes must score at least target_vmaf - VMAF_MARGIN
    (else MIN_VMAF) on those excerpts.

    Returns:
        Input size, re-encoded size and elapsed seconds, whether the re-encode was
        published, and a note with the quality used and the re-encode's VMAF.
    """
    if quality is not None and target_vmaf is not None:
        raise ValueError(f"Pass only one of {quality=} and {target_vmaf=}")
    if not os.path.isfile(input_file):
        raise FileNotFoundError(input_file)
    if os.path.realpath(input_file) == os.path.realpath(output_file):
        raise ValueError("Input and output paths must differ")
    if os.path.exists(output_file) and not overwrite:
        raise FileExistsError(f"{output_file} already exists; pass --overwrite to replace it")

    source_probe = probe_video(ffprobe, input_file)
    stream_position, video_stream = primary_video_stream(source_probe)
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if reason := skip_reason(video_stream):
        if keep_original:  # keep the output directory complete, as for rejected re-encodes
            shutil.copyfile(input_file, output_file)
            copy_macos_metadata(input_file, output_file)
        raise SkipVideo(reason)
    hdr_side_data = [name for name in HDR_SIDE_DATA if side_data(video_stream, name)]
    if encoder == "x265" and hdr_side_data:
        raise ValueError(
            f"x265 would drop {', '.join(hdr_side_data)}; use the videotoolbox encoder"
        )

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=".compress-video-", dir=output_dir) as tmpdir:
        encoded_file = f"{tmpdir}/encoded.mp4"
        rebuilt_file = f"{tmpdir}/rebuilt.mp4"
        windows = sample_windows(float(source_probe["format"]["duration"]))
        if target_vmaf is not None:
            quality, _ = choose_quality(
                ffmpeg,
                input_file,
                tmpdir,
                stream_position=stream_position,
                source_stream=video_stream,
                windows=windows,
                target_vmaf=target_vmaf,
                start_quality=ENCODERS[encoder][0],
                speed_priority=speed_priority,
                encoder=encoder,
                ten_bit=ten_bit,
            )
        elif quality is None:
            raise ValueError("Pass a fixed quality or a target_vmaf")
        encode_video(
            ffmpeg,
            input_file,
            encoded_file,
            stream_position=stream_position,
            source_stream=video_stream,
            quality=quality,
            speed_priority=speed_priority,
            encoder=encoder,
            ten_bit=ten_bit,
            quiet=quiet,
        )
        replace_video_track(
            mp4box,
            input_file,
            encoded_file,
            rebuilt_file,
            source_probe=source_probe,
            stream_position=stream_position,
        )
        source_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(rebuilt_file)
        accepted = compressed_size <= source_size * (1 - MIN_SIZE_REDUCTION)
        note = f"quality {quality}"
        if accepted:
            verify_rebuilt(
                input_file,
                rebuilt_file,
                source_probe=source_probe,
                stream_position=stream_position,
                ten_bit=ten_bit,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
            )
            # catch broken or blocky encodes: score the same excerpts of the final video
            floor = MIN_VMAF if target_vmaf is None else target_vmaf - VMAF_MARGIN
            final_vmaf = min(
                vmaf_score(
                    ffmpeg,
                    input_file,
                    encoded_file,
                    stream_position=stream_position,
                    window=window,
                    distorted_is_excerpt=False,
                    width=video_stream["width"],
                )
                for window in windows
            )
            if final_vmaf < floor:
                raise RuntimeError(
                    f"Quality check failed: VMAF {final_vmaf:.1f} < {floor:.1f}"
                )
            note += f", VMAF {final_vmaf:.1f}"
        elif keep_original:
            shutil.copyfile(input_file, rebuilt_file)
        if accepted or keep_original:
            os.replace(rebuilt_file, output_file)
            copy_macos_metadata(input_file, output_file)

    return source_size, compressed_size, time.perf_counter() - started, accepted, note


def report_result(
    source_size: int,
    compressed_size: int,
    elapsed: float,
    *,
    accepted: bool,
    outdir: str | None,
    note: str,
) -> None:
    """Print the size change of one published or rejected re-encode."""
    reduction = 100 * (1 - compressed_size / source_size)
    sizes = f"{source_size / 1e6:.1f} MB -> {compressed_size / 1e6:.1f} MB"
    if accepted:
        print(f"  {sizes} ({reduction:.1f}% smaller, {note}) in {elapsed:.1f}s")
    else:
        kept = "copied original instead" if outdir else "no output written"
        print(
            f"  Rejected: {sizes} is only {reduction:.1f}% smaller "
            f"(< {MIN_SIZE_REDUCTION:.0%}), {kept}"
        )


def main(
    source_files: Sequence[str],
    outdir: str | None = None,
    suffix: str = "-compressed",
    *,
    write_file_map: bool = False,
    on_error: Literal["raise", "print"] = "raise",
    quality: int | None = None,
    speed_priority: bool = True,
    overwrite: bool = False,
    jobs: int = DEFAULT_JOBS,
    target_vmaf: float = DEFAULT_TARGET_VMAF,
    encoder: Encoder = "videotoolbox",
    ten_bit: bool = True,
) -> int:
    """Compress videos while preserving container, stream, and filesystem metadata.

    Each video gets the smallest-file quality reaching target_vmaf, unless a fixed
    quality is given (faster, no per-video search).

    Re-encodes saving less than MIN_SIZE_REDUCTION are rejected. With outdir, the
    original is copied there instead so the output directory stays complete; with a
    suffix, the original already sits next to where the output would go, so nothing is
    written.
    """
    max_quality = ENCODERS[encoder][4]
    if quality is not None and not 0 <= quality <= max_quality:
        raise ValueError(f"{encoder} quality must be in 0..{max_quality}, got {quality}")
    if jobs < 1:
        raise ValueError(f"jobs must be at least 1, got {jobs}")
    if outdir:
        os.makedirs(outdir, exist_ok=True)

    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    mp4box = require_tool("MP4Box")
    for tool in ("GetFileInfo", "SetFile"):  # copy_macos_metadata restores creation dates
        require_tool(tool)
    in_out_map: dict[str, str] = {}
    failures = 0
    out_paths = {
        file_path: output_path(file_path, outdir, suffix) for file_path in source_files
    }

    def compress(file_path: str) -> tuple[int, int, float, bool, str]:
        """Compress one file with this run's settings."""
        return compress_video(
            file_path,
            out_paths[file_path],
            quality=quality,
            speed_priority=speed_priority,
            overwrite=overwrite,
            keep_original=bool(outdir),
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            mp4box=mp4box,
            target_vmaf=None if quality is not None else target_vmaf,
            encoder=encoder,
            ten_bit=ten_bit,
            quiet=jobs > 1,  # concurrent progress lines would overwrite each other
        )

    # Apple silicon has several media engines, so files can encode concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(compress, file_path): file_path for file_path in source_files
        }
        for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            file_path = futures[future]
            out_path = out_paths[file_path]
            print(
                f"Compressed {idx}/{len(source_files)}: {file_path} -> {out_path}", flush=True
            )
            try:
                source_size, compressed_size, elapsed, accepted, note = future.result()
            except SkipVideo as reason:
                print(f"  Skipped: {reason}" + (", copied original instead" if outdir else ""))
                if outdir:
                    in_out_map[file_path] = out_path
                continue
            except Exception as exc:
                failures += 1
                if on_error == "raise":
                    for pending in futures:
                        pending.cancel()
                    raise
                print(f"{file_path}: {exc}", file=sys.stderr)
                continue

            report_result(
                source_size,
                compressed_size,
                elapsed,
                accepted=accepted,
                outdir=outdir,
                note=note,
            )
            if accepted or outdir:
                in_out_map[file_path] = out_path
    in_out_map = {path: in_out_map[path] for path in source_files if path in in_out_map}

    if write_file_map:
        file_map_path = f"{outdir or os.getcwd()}/file_map.json"
        with open(file_map_path, "w", encoding="utf-8") as json_file:
            json.dump(in_out_map, json_file, indent=2)
        print(f"A map from input to output file paths was written to {file_map_path}")

    return int(failures > 0)


if __name__ == "__main__":
    import argparse

    with open(f"{os.path.dirname(__file__)}/compress-videos.md", encoding="utf-8") as md_file:
        parser = argparse.ArgumentParser(description=md_file.read())
    parser.add_argument("source_files", nargs="+", help="Video files to be compressed")

    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        *("-o", "--outdir"),
        help="Output directory where compressed files will be created. New files will "
        "have the same basename as the original file.",
    )
    out_group.add_argument(
        *("-s", "--suffix"),
        default="-compressed",
        help="Suffix to append to the original filename to create the output filename. "
        "E.g. --suffix=-compressed gives input.mp4 -> input-compressed.mp4. "
        "Defaults to -compressed when --outdir is omitted.",
    )
    parser.add_argument(
        "--write-file-map",
        action="store_true",
        help="Write JSON file mapping input to output file paths to outdir (or the cwd).",
    )
    parser.add_argument(
        "--on-error",
        choices=("raise", "print"),
        default="raise",
        help="'raise' stops at the first error. 'print' reports it to stderr, continues "
        "with the next file and exits non-zero at the end.",
    )
    parser.add_argument(
        *("-q", "--quality"),
        type=int,
        help="Fixed quality for all videos instead of the per-video VMAF search (about 10x "
        "faster). VideoToolbox -q:v from 0 to 100, higher is better and larger (10-bit "
        "needs about 10 less than 8-bit for the same VMAF). x265 -crf from 0 to 51, lower "
        "is better and larger.",
    )
    parser.add_argument(
        "--encoder",
        choices=tuple(ENCODERS),
        default="videotoolbox",
        help="videotoolbox: Apple media engine. x265: CPU, about 3x slower but about 40%% "
        "smaller at equal VMAF on 4K drone footage. x265 refuses HDR videos.",
    )
    parser.add_argument(
        "--eight-bit",
        action="store_false",
        dest="ten_bit",
        help="Keep 8-bit sources 8-bit instead of encoding them as 10-bit Main10.",
    )
    parser.add_argument(
        "--quality-priority",
        action="store_false",
        dest="speed_priority",
        help="Favor encoder quality over speed. VideoToolbox: about 1.9x rather than "
        "3.4x real-time on the tested M4 Pro, with a small quality improvement. "
        "x265: preset slow instead of medium.",
    )
    parser.add_argument(
        "--target-vmaf",
        type=float,
        default=DEFAULT_TARGET_VMAF,
        help="Pick the quality per video: the smallest file whose sampled excerpts all "
        f"reach this VMAF. Defaults to {DEFAULT_TARGET_VMAF:g} (near-transparent).",
    )
    parser.add_argument(
        *("-j", "--jobs"),
        type=int,
        default=DEFAULT_JOBS,
        help=f"Files to encode concurrently. Defaults to {DEFAULT_JOBS}.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing output files only after a new result passes verification.",
    )
    raise SystemExit(main(**vars(parser.parse_args())))
