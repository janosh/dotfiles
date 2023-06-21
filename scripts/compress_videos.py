from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Sequence

__author__ = "Janosh Riebesell"
__date__ = "2022-07-04"

DIRNAME = os.path.dirname(__file__)


"""
Example invocation:
python ~/dev/macos-setup/scripts/compress_videos.py src-dir/*.mp4 --outdir outdir
"""


def handbrake_h265_vtb_encode(
    input_file: str, output_file: str, *args: str | int | None
) -> None:
    """Compress input_file to output_file with HandBrakeCLI using vt_h265 (Apple's
    Video Toolbox H265 encoder). https://developer.apple.com/documentation/videotoolbox

    Run handbrakeCLI --help for docs.
    """
    # uses 'H265 Videotoolbox' encode preset exported as JSON from Handbrake GUI
    # https://superuser.com/a/1031023
    cmd = ["handbrakeCLI", "--preset-import-file", f"{DIRNAME}/h265-videotoolbox.json"]
    # preset must be explicitly set even after importing
    cmd += ["--preset", "H265 Videotoolbox"]
    cmd += ["--input", input_file, "--output", output_file, *args]

    result = subprocess.run(cmd, capture_output=True)

    if result.stderr:
        print(result.stderr.decode("utf-8"), file=sys.stderr)


def copy_original_metadata(input_file: str, output_file: str) -> None:
    """Copies metadata from original video input_file to compressed output_file."""
    # extractEmbedded: finds embedded metadata like GPS tracks
    # https://stackoverflow.com/a/58958944
    cmd = ["exiftool", "-tagsFromFile", input_file, "-extractEmbedded", "-all:all"]
    cmd += ["-FileModifyDate", "-overwrite_original", output_file]

    subprocess.run(cmd, capture_output=True, check=True)


def main(
    source_files: Sequence[str],
    outdir: str,
    write_file_map: bool = False,
    on_error: Literal["raise", "print", "ignore"] = "raise",
    quality: int | None = None,
) -> int:
    """Compress videos using HandBrakeCLI and copy metadata using exiftool.

    Args:
        source_files (Sequence[str]): Video files to compress.
        outdir (str): Directory to write compressed files to.
        write_file_map (bool, optional): Write JSON file mapping input to output file paths
            to outdir. Defaults to False.
        on_error (Literal[&quot;raise&quot;, &quot;print&quot;, &quot;ignore&quot;], optional):
            What to do if an error occurs. If 'raise', will exit non-zero. If 'print' will
            print error to stderr, then continue with next file. If 'ignore' directly
            continues with next file. Defaults to 'raise'.
        quality (int | None, optional): Quality setting for HandBrakeCLI. Defaults to None.

    Raises:
        ValueError: If outdir is a file, not a directory or if no input files are received
            or if on_error is not one of 'raise', 'print' or 'ignore'.

    Returns:
        int: exit code (0 if successful)
    """
    if os.path.isfile(outdir):
        raise ValueError(
            f"{outdir=} must be a (possibly non-existent) directory, not a file"
        )
    if len(source_files) == 0:
        raise ValueError("No input files received")

    os.makedirs(outdir, exist_ok=True)

    in_out_map: dict[str, str] = {}

    for idx, file_path in enumerate(source_files, 1):
        basename = os.path.basename(file_path)
        out_path = f"{outdir.removesuffix('/')}/{basename}"
        print(f"Compressing {idx}/{len(source_files)}: {file_path}->{out_path}")

        try:
            handbrake_h265_vtb_encode(file_path, out_path, "--quality", str(quality))
            copy_original_metadata(file_path, out_path)
        except Exception as exc:
            if on_error == "raise":
                raise
            if on_error == "print":
                print(exc, file=sys.stderr)
                continue
            if on_error == "ignore":
                continue
            raise ValueError(
                f"Unexpected {on_error=}, should be 'raise', 'print' or 'ignore'"
            )
        in_out_map[file_path] = out_path

    if write_file_map:
        import json

        file_map_path = f"{outdir}/file_map.json"
        with open(file_map_path, "w") as json_file:
            json.dump(in_out_map, json_file)
        print(f"A map from input to output file paths was written to {file_map_path}")

    return 0


if __name__ == "__main__":
    import argparse

    try:
        with open(f"{DIRNAME}/compress-videos.md") as md_file:
            description = md_file.read()
    except FileNotFoundError:
        description = ""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("source_files", nargs="+", help="Video files to be compressed")
    parser.add_argument(
        *("-o", "--outdir"),
        help="Output directory where compressed files will be created. New files will "
        "have the same basename as the original file.",
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
        default=42,  # see h265-videotoolbox.json
        help="Quality of the output video. Higher is better but means larger file size."
        " Quite sensitive. Corresponds to the value of VideoQualitySlider in "
        "h265-videotoolbox.json. Cranking this up to 60 will result in larger output "
        "than input file. Defaults to 42",
    )
    args = parser.parse_args()

    ret_code = main(**vars(args))
    raise SystemExit(ret_code)
