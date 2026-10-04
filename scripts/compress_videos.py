"""Compress videos with VideoToolbox while retaining the original MP4 metadata."""

from __future__ import annotations

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

DEFAULT_QUALITY = 62
MIN_SIZE_REDUCTION = 0.1  # re-encodes saving less are rejected
MAX_QUALITY = 100
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
AUXILIARY_STREAM_KEYS = (
    "id",
    "codec_type",
    "codec_name",
    "codec_tag_string",
    "duration",
    "nb_frames",
    "tags",
    "disposition",
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
    return json.loads(
        run_command(
            [
                ffprobe,
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                file_path,
            ],
            capture_output=True,
        )
    )


def presentation_timestamps(
    ffprobe: str, file_path: str, stream_position: int, time_base: str
) -> list[Fraction]:
    """Return exact presentation times of video packets not marked for discard."""
    packet_probe = json.loads(
        run_command(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                str(stream_position),
                "-show_packets",
                "-show_entries",
                "packet=pts,flags",
                "-of",
                "json",
                file_path,
            ],
            capture_output=True,
        )
    )
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
) -> None:
    """Encode one video stream as HEVC using Apple's hardware media engine."""
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

    command = [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-hwaccel",
        "videotoolbox",
        "-hwaccel_output_format",
        "videotoolbox_vld",
        "-noautorotate",
        "-i",
        input_file,
        "-map",
        f"0:{stream_position}",
        "-map_metadata",
        "0",
        "-c:v",
        "hevc_videotoolbox",
        "-q:v",
        str(quality),
        "-prio_speed",
        str(int(speed_priority)),
        "-spatial_aq",
        "1",
        "-fps_mode",
        "passthrough",
        "-enc_time_base:v",
        source_stream["time_base"],
        "-tag:v",
        "hvc1",
    ]
    if color_metadata:
        command.extend(("-bsf:v", f"hevc_metadata={':'.join(color_metadata)}"))
    command.append(output_file)
    run_command(command)


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


def copy_macos_metadata(input_file: str, output_file: str) -> None:
    """Copy filesystem timestamps, mode, flags, and macOS extended attributes."""
    source_stat = os.stat(input_file, follow_symlinks=False)
    shutil.copystat(input_file, output_file, follow_symlinks=False)
    os.chown(
        output_file,
        source_stat.st_uid,
        source_stat.st_gid,
        follow_symlinks=False,
    )

    for name in run_command(["xattr", input_file], capture_output=True).splitlines():
        hex_value = run_command(["xattr", "-px", name, input_file], capture_output=True)
        run_command(
            ["xattr", "-wx", name, "".join(hex_value.split()), output_file],
            capture_output=True,
        )

    # Extended-attribute tools can update these, so restore access/modify times next.
    os.utime(
        output_file,
        ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns),
        follow_symlinks=False,
    )

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


def verify_output(
    source_probe: dict[str, Any],
    output_probe: dict[str, Any],
    stream_position: int,
) -> None:
    """Verify video properties, container tags, and all non-video streams."""
    source_video = source_probe["streams"][stream_position]
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

    for key in (
        "width",
        "height",
        "pix_fmt",
        "color_range",
        "color_space",
        "color_transfer",
        "color_primaries",
    ):
        if source_video.get(key) != output_video.get(key):
            raise RuntimeError(
                f"Video property {key!r} changed from {source_video.get(key)!r} "
                f"to {output_video.get(key)!r}"
            )

    if display_matrix(source_video) != display_matrix(output_video):
        raise RuntimeError("Video display matrix changed")

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
    quality: int,
    speed_priority: bool,
    overwrite: bool,
    keep_original: bool,
    ffmpeg: str,
    ffprobe: str,
    mp4box: str,
) -> tuple[int, int, float, bool]:
    """Compress one video and atomically publish the verified result.

    A result saving less than MIN_SIZE_REDUCTION is discarded unverified. With
    keep_original, a copy of the input is published in its place.

    Returns:
        Input size, re-encoded size and elapsed seconds, and whether the re-encode was
        published.
    """
    if not os.path.isfile(input_file):
        raise FileNotFoundError(input_file)
    if os.path.realpath(input_file) == os.path.realpath(output_file):
        raise ValueError("Input and output paths must differ")
    if os.path.exists(output_file) and not overwrite:
        raise FileExistsError(f"{output_file} already exists; pass --overwrite to replace it")

    source_probe = probe_video(ffprobe, input_file)
    stream_position, video_stream = primary_video_stream(source_probe)
    output_dir = os.path.dirname(os.path.abspath(output_file))

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=".compress-video-", dir=output_dir) as tmpdir:
        encoded_file = f"{tmpdir}/encoded.mp4"
        rebuilt_file = f"{tmpdir}/rebuilt.mp4"
        encode_video(
            ffmpeg,
            input_file,
            encoded_file,
            stream_position=stream_position,
            source_stream=video_stream,
            quality=quality,
            speed_priority=speed_priority,
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
        if accepted:
            output_probe = probe_video(ffprobe, rebuilt_file)
            verify_output(source_probe, output_probe, stream_position)
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
        elif keep_original:
            shutil.copyfile(input_file, rebuilt_file)
        if accepted or keep_original:
            os.replace(rebuilt_file, output_file)
            copy_macos_metadata(input_file, output_file)

    return source_size, compressed_size, time.perf_counter() - started, accepted


def main(
    source_files: Sequence[str],
    outdir: str | None = None,
    suffix: str = "-compressed",
    *,
    write_file_map: bool = False,
    on_error: Literal["raise", "print", "ignore"] = "raise",
    quality: int = DEFAULT_QUALITY,
    speed_priority: bool = True,
    overwrite: bool = False,
) -> int:
    """Compress videos while preserving container, stream, and filesystem metadata.

    Re-encodes saving less than MIN_SIZE_REDUCTION are rejected. With outdir, the
    original is copied there instead so the output directory stays complete; with a
    suffix, the original already sits next to where the output would go, so nothing is
    written.
    """
    if not 0 <= quality <= MAX_QUALITY:
        raise ValueError(f"quality must be between 0 and {MAX_QUALITY}, got {quality}")
    if outdir:
        os.makedirs(outdir, exist_ok=True)

    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    mp4box = require_tool("MP4Box")
    for tool in ("GetFileInfo", "SetFile"):  # copy_macos_metadata restores creation dates
        require_tool(tool)
    in_out_map: dict[str, str] = {}
    failures = 0

    for idx, file_path in enumerate(source_files, start=1):
        out_path = output_path(file_path, outdir, suffix)
        print(f"Compressing {idx}/{len(source_files)}: {file_path} -> {out_path}", flush=True)

        try:
            source_size, compressed_size, elapsed, accepted = compress_video(
                file_path,
                out_path,
                quality=quality,
                speed_priority=speed_priority,
                overwrite=overwrite,
                keep_original=bool(outdir),
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
                mp4box=mp4box,
            )
        except Exception as exc:
            failures += 1
            if on_error == "raise":
                raise
            if on_error == "print":
                print(f"{file_path}: {exc}", file=sys.stderr)
            continue

        reduction = 100 * (1 - compressed_size / source_size)
        sizes = f"{source_size / 1e6:.1f} MB -> {compressed_size / 1e6:.1f} MB"
        if accepted:
            print(f"  {sizes} ({reduction:.1f}% smaller) in {elapsed:.1f}s")
        else:
            kept = "copied original instead" if outdir else "no output written"
            print(
                f"  Rejected: {sizes} is only {reduction:.1f}% smaller "
                f"(< {MIN_SIZE_REDUCTION:.0%}), {kept}"
            )
        if accepted or outdir:
            in_out_map[file_path] = out_path

    if write_file_map:
        file_map_path = f"{outdir or os.getcwd()}/file_map.json"
        with open(file_map_path, "w", encoding="utf-8") as json_file:
            json.dump(in_out_map, json_file, indent=2)
        print(f"A map from input to output file paths was written to {file_map_path}")

    return int(failures > 0 and on_error != "ignore")


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
        choices=("raise", "print", "ignore"),
        default="raise",
        help="What to do if an error occurs. If 'raise', will exit non-zero. If "
        "'print' will print error to stderr, then continue with next file. If "
        "'ignore' directly continues with next file.",
    )
    parser.add_argument(
        *("-q", "--quality"),
        type=int,
        default=DEFAULT_QUALITY,
        help="VideoToolbox quality from 0 to 100. Higher is better and larger. "
        f"Defaults to {DEFAULT_QUALITY}.",
    )
    parser.add_argument(
        "--quality-priority",
        action="store_false",
        dest="speed_priority",
        help="Favor encoder quality over speed. About 1.9x rather than 3.4x real-time "
        "on the tested M4 Pro, with a small quality improvement.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing output files only after a new result passes verification.",
    )
    raise SystemExit(main(**vars(parser.parse_args())))
