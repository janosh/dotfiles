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

DIRNAME = os.path.dirname(__file__)
DEFAULT_QUALITY = 62
MAX_QUALITY = 100
DISPLAY_MATRIX_VALUES = 9
FRAME_RATE_TOLERANCE = 0.01
COLOR_PRIMARIES = {
    "bt709": 1,
    "bt470m": 4,
    "bt470bg": 5,
    "smpte170m": 6,
    "smpte240m": 7,
    "bt2020": 9,
    "smpte431": 11,
    "smpte432": 12,
}
COLOR_TRANSFERS = {
    "bt709": 1,
    "bt470m": 4,
    "bt470bg": 5,
    "smpte170m": 6,
    "smpte240m": 7,
    "iec61966-2-1": 13,
    "bt2020-10": 14,
    "bt2020-12": 15,
    "smpte2084": 16,
    "arib-std-b67": 18,
}
COLOR_MATRICES = {
    "rgb": 0,
    "bt709": 1,
    "fcc": 4,
    "bt470bg": 5,
    "smpte170m": 6,
    "smpte240m": 7,
    "bt2020nc": 9,
    "bt2020c": 10,
}


def require_tool(name: str) -> str:
    """Return the absolute path to a required executable."""
    if path := shutil.which(name):
        return path
    raise RuntimeError(
        f"Required executable {name!r} was not found. "
        "Install dependencies with `brew install ffmpeg gpac`."
    )


def run_checked(command: Sequence[str], *, capture_output: bool = False) -> None:
    """Run a command and include captured diagnostics in failures."""
    result = subprocess.run(
        command,
        capture_output=capture_output,
        check=False,
        text=True,
    )
    if result.returncode == 0:
        return

    diagnostics = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part)
    message = f"Command failed ({result.returncode}): {' '.join(command)}"
    if diagnostics:
        message += f"\n{diagnostics}"
    raise RuntimeError(message)


def command_output(command: Sequence[str]) -> str:
    """Run a command and return its stdout."""
    return subprocess.run(
        command,
        capture_output=True,
        check=True,
        text=True,
    ).stdout


def probe_video(ffprobe: str, file_path: str) -> dict[str, Any]:
    """Return all stream and container metadata reported by FFprobe."""
    return json.loads(
        command_output(
            [
                ffprobe,
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                file_path,
            ]
        )
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
        "-tag:v",
        "hvc1",
    ]
    if color_metadata:
        command.extend(("-bsf:v", f"hevc_metadata={':'.join(color_metadata)}"))
    command.append(output_file)
    run_checked(command)


def replace_video_track(
    mp4box: str,
    input_file: str,
    encoded_file: str,
    output_file: str,
    *,
    source_probe: dict[str, Any],
    stream_position: int,
    source_track_id: int,
) -> None:
    """Replace only the primary video track, retaining every other MP4 box and track."""
    existing_ids = [
        int(str(stream["id"]), 0)
        for stream in source_probe["streams"]
        if stream.get("id") is not None
    ]
    temporary_track_id = max(existing_ids, default=0) + 1
    imported_track = (
        f"{encoded_file}#trackID=1:ID={temporary_track_id}:tkidx={stream_position + 1}"
    )
    run_checked(
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
    matrix = display_matrix(source_probe["streams"][stream_position])
    if matrix:
        run_checked(
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

    if sys.platform == "darwin" and (xattr := shutil.which("xattr")):
        for name in command_output([xattr, input_file]).splitlines():
            value = (
                command_output([xattr, "-px", name, input_file])
                .replace(" ", "")
                .replace("\n", "")
            )
            run_checked([xattr, "-wx", name, value, output_file], capture_output=True)

    # Extended-attribute tools can update these, so restore access/modify times next.
    os.utime(
        output_file,
        ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns),
        follow_symlinks=False,
    )

    # Setting an mtime older than the creation date can lower the latter on APFS.
    # Restore the original creation date only after the final os.utime call.
    if (
        sys.platform == "darwin"
        and (get_file_info := shutil.which("GetFileInfo"))
        and (set_file := shutil.which("SetFile"))
    ):
        creation_date = command_output([get_file_info, "-d", input_file]).strip()
        run_checked([set_file, "-d", creation_date, output_file], capture_output=True)


def stream_signature(stream: dict[str, Any]) -> dict[str, Any]:
    """Return stable fields used to verify untouched auxiliary streams."""
    return {
        key: stream.get(key)
        for key in (
            "id",
            "codec_type",
            "codec_name",
            "codec_tag_string",
            "duration",
            "nb_frames",
            "tags",
            "disposition",
        )
    }


def auxiliary_signatures(probe: dict[str, Any], stream_position: int) -> list[dict[str, Any]]:
    """Return stable signatures for every stream except the primary video."""
    return [
        stream_signature(stream)
        for position, stream in enumerate(probe["streams"])
        if position != stream_position
    ]


def verify_output(
    source_probe: dict[str, Any],
    output_probe: dict[str, Any],
    stream_position: int,
) -> None:
    """Verify video properties, container tags, and all non-video streams."""
    source_position, source_video = primary_video_stream(source_probe)
    output_position, output_video = primary_video_stream(output_probe)
    if source_position != stream_position or output_position != stream_position:
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

    source_frame_rate = Fraction(source_video["avg_frame_rate"])
    output_frame_rate = Fraction(output_video["avg_frame_rate"])
    if abs(float(source_frame_rate - output_frame_rate)) > FRAME_RATE_TOLERANCE:
        raise RuntimeError(
            f"Frame rate changed from {float(source_frame_rate):.6f} "
            f"to {float(output_frame_rate):.6f}"
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

    duration_tolerance = max(0.05, float(2 / source_frame_rate))
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


def output_path(input_file: str, outdir: str | None, suffix: str | None) -> str:
    """Build an output path without changing the source extension."""
    if outdir:
        return os.path.join(outdir, os.path.basename(input_file))
    if suffix is None:
        raise ValueError("Either outdir or suffix must be provided")
    stem, extension = os.path.splitext(input_file)
    return f"{stem}{suffix}{extension}"


def compress_video(
    input_file: str,
    output_file: str,
    *,
    quality: int,
    speed_priority: bool,
    overwrite: bool,
    ffmpeg: str,
    ffprobe: str,
    mp4box: str,
) -> tuple[int, int, float]:
    """Compress one video and atomically publish the verified result."""
    if not os.path.isfile(input_file):
        raise FileNotFoundError(input_file)
    if os.path.realpath(input_file) == os.path.realpath(output_file):
        raise ValueError("Input and output paths must differ")
    if os.path.exists(output_file) and not overwrite:
        raise FileExistsError(f"{output_file} already exists; pass --overwrite to replace it")

    source_probe = probe_video(ffprobe, input_file)
    stream_position, video_stream = primary_video_stream(source_probe)
    source_track_id = track_id(video_stream)
    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=".compress-video-", dir=output_dir) as tmpdir:
        encoded_file = os.path.join(tmpdir, "encoded.mp4")
        rebuilt_file = os.path.join(tmpdir, "rebuilt.mp4")
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
            source_track_id=source_track_id,
        )
        verify_output(source_probe, probe_video(ffprobe, rebuilt_file), stream_position)
        os.replace(rebuilt_file, output_file)

    copy_macos_metadata(input_file, output_file)
    return (
        os.path.getsize(input_file),
        os.path.getsize(output_file),
        time.perf_counter() - started,
    )


def main(
    source_files: Sequence[str],
    outdir: str | None = None,
    suffix: str | None = None,
    *,
    write_file_map: bool = False,
    on_error: Literal["raise", "print", "ignore"] = "raise",
    quality: int = DEFAULT_QUALITY,
    speed_priority: bool = True,
    overwrite: bool = False,
) -> int:
    """Compress videos while preserving container, stream, and filesystem metadata."""
    if not source_files:
        raise ValueError("No input files received")
    if not outdir and suffix is None:
        raise ValueError("Either outdir or suffix must be provided")
    if not 0 <= quality <= MAX_QUALITY:
        raise ValueError(f"quality must be between 0 and {MAX_QUALITY}, got {quality}")
    if on_error not in {"raise", "print", "ignore"}:
        raise ValueError(f"Unexpected {on_error=}")

    if outdir:
        if os.path.isfile(outdir):
            raise ValueError(
                f"{outdir=} must be a (possibly non-existent) directory, not a file"
            )
        os.makedirs(outdir, exist_ok=True)

    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    mp4box = require_tool("MP4Box")
    in_out_map: dict[str, str] = {}
    failures = 0

    for idx, file_path in enumerate(source_files, start=1):
        out_path = output_path(file_path, outdir, suffix)
        print(f"Compressing {idx}/{len(source_files)}: {file_path} -> {out_path}", flush=True)

        try:
            source_size, compressed_size, elapsed = compress_video(
                file_path,
                out_path,
                quality=quality,
                speed_priority=speed_priority,
                overwrite=overwrite,
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
        print(
            f"  {source_size / 1e6:.1f} MB -> {compressed_size / 1e6:.1f} MB "
            f"({reduction:.1f}% smaller) in {elapsed:.1f}s"
        )
        if compressed_size >= source_size:
            print("  Warning: compressed file is not smaller than its source", file=sys.stderr)
        in_out_map[file_path] = out_path

    if write_file_map:
        map_dir = outdir or os.getcwd()
        file_map_path = os.path.join(map_dir, "file_map.json")
        with open(file_map_path, "w") as json_file:
            json.dump(in_out_map, json_file, indent=2)
        print(f"A map from input to output file paths was written to {file_map_path}")

    return int(failures > 0 and on_error != "ignore")


if __name__ == "__main__":
    import argparse

    try:
        with open(f"{DIRNAME}/compress-videos.md") as md_file:
            description = md_file.read()
    except FileNotFoundError:
        description = ""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("source_files", nargs="+", help="Video files to be compressed")

    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        *("-o", "--outdir"),
        help="Output directory where compressed files will be created. New files will "
        "have the same basename as the original file.",
    )
    out_group.add_argument(
        *("-s", "--suffix"),
        help="Suffix to append to the original filename to create the output filename. "
        "E.g. --suffix=-compressed gives input.mp4 -> input-compressed.mp4. "
        "Defaults to -compressed when --outdir is omitted.",
    )
    parser.add_argument(
        "--write-file-map",
        action="store_true",
        help="Write JSON file mapping input to output file paths to outdir.",
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
    args = parser.parse_args()
    if not args.outdir and args.suffix is None:
        args.suffix = "-compressed"

    raise SystemExit(main(**vars(args)))
