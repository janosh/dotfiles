"""Compress screenshots dropped into ~/Desktop, then move them to ~/Downloads.

PNG files wider than 2000px are downscaled, then shrunk with pngquant and zopflipng; JPGs are
re-saved with Pillow. Run from a Folder Action ('Folder Actions Setup.app') watching
~/Desktop with inputs passed as arguments:
    python3 ~/dev/dotfiles/scripts/compress_screenshots.py "$@"
Requires: brew install pngquant zopfli imagemagick && pip install pillow
If the action never triggers, toggle "Enable Folder Actions" in that app.
"""

import os
import sys
import traceback
from datetime import UTC, datetime
from shutil import which
from subprocess import run

from PIL import Image

HOME = os.path.expanduser("~")
EXTS = (".png", ".jpg", ".jpeg")


def compress_png(file_path: str, tools: dict[str, str]) -> None:
    """Downscale a PNG to at most 2000px wide, then losslessly shrink it in place."""
    # check=False: pngquant exits 98/99 when the result would not be smaller
    run(
        [tools["pngquant"], "32", "--skip-if-larger", "--ext", ".png", "--force", file_path],
        capture_output=True,
        check=False,
    )
    # '>' only shrinks (no shell here, so no quotes around it)
    run([tools["mogrify"], "-resize", "2000>", file_path], capture_output=True, check=False)
    run([tools["zopflipng"], "-y", file_path, file_path], capture_output=True, check=False)


def compress_jpg(file_path: str) -> None:
    """Re-save a JPG in place at quality 75."""
    Image.open(file_path).save(file_path, quality=75, optimize=True)


os.environ["PATH"] += ":/opt/homebrew/bin"  # Folder Actions run with a minimal PATH
try:
    tools = {name: which(name) or "" for name in ("pngquant", "mogrify", "zopflipng")}
    if missing := [name for name, path in tools.items() if not path]:
        raise ImportError(f"Missing required binaries: {', '.join(missing)}")

    for file_path in sys.argv[1:]:
        stem, ext = os.path.splitext(file_path)
        if ext.lower() not in EXTS:
            continue
        if ext != ext.lower():  # normalize e.g. .PNG -> .png and .JPEG -> .jpg
            new_path = stem + (".jpg" if ext.lower() == ".jpeg" else ext.lower())
            os.replace(file_path, new_path)
            file_path = new_path  # noqa: PLW2901

        if file_path.endswith(".png"):
            compress_png(file_path, tools)
        else:
            compress_jpg(file_path)
        os.rename(file_path, f"{HOME}/Downloads/{os.path.basename(file_path)}")

except (ImportError, OSError, ValueError):
    with open(f"{HOME}/Downloads/compress-screenshot.log", "a", encoding="utf-8") as log:
        now = datetime.now(tz=UTC).astimezone()
        log.write(f"{now:%H:%M:%S}\n{sys.executable=}\n{os.environ['PATH']=}\n")
        log.write(f"{traceback.format_exc()}\n")
