import os
import sys
import traceback
from datetime import datetime
from os.path import basename, expanduser
from shutil import which
from subprocess import run

from PIL import Image

# Use this script by creating a new folder action with 'Folder Actions Setup.app' that
# watches '~/Desktop' (pass inputs as arguments!) and runs this shell script:
# ```sh
# source ~/.zshrc # can be omitted if the system python3 is 3.9+
# python3 ~/dev/macos-setup/scripts/compress-screenshots.py "$@"
# ```

# Requires: brew install pngquant zopfli imagemagick && pip install Pillow

# If folder action doesn't appear to trigger after setup, try toggling
# "Enable Folder Actions" in "Folder Actions Setup.app" or add one of the
# default actions and see if that runs.

HOME = expanduser("~")
EXTS = (".png", ".jpg", ".jpeg")


def compress_png(file: str) -> None:
    # don't move file inside ''.split() so as not to split on spaces in filename

    # set check=False to not raise on non-zero exit code as pngquant returns code
    # 98/99 if processed file is not smaller
    run(
        f"{pngquant} 32 --skip-if-larger --ext .png --force".split() + [file],
        check=False,
        capture_output=True,
    )

    run(f"{mogrify} -resize '2000>'".split() + [file], capture_output=True)

    run(f"{zopflipng} -y".split() + [file, file], capture_output=True)


def compress_jpg(file: str) -> None:
    img = Image.open(file)
    img.save(file, quality=75, optimize=True)


os.environ["PATH"] += ":/opt/homebrew/bin"
clis = [which(x) for x in ("pngquant", "mogrify", "zopflipng")]

pngquant, mogrify, zopflipng = clis

try:
    for cli in clis:
        if cli is None:
            raise ImportError(f"Missing required binary: {cli}")

    for file in sys.argv[1:]:  # first arg is this script's name
        ext = os.path.splitext(file)[1]
        if ext.lower() != ext and ext.lower() in EXTS:
            if ext.lower() == ".jpeg":
                ext = ".jpg"
            newName = os.path.splitext(file)[0] + ext.lower()
            os.replace(file, newName)

        if not file.endswith(EXTS):
            continue

        compress_png(file) if file.lower().endswith(".png") else compress_jpg(file)
        os.rename(file, f"{HOME}/Downloads/{basename(file)}")

except Exception:
    with open(f"{HOME}/Desktop/compress-screenshot.log", "a") as logs:
        now = datetime.now()
        PATH = os.environ["PATH"]

        logs.write(
            f"{now:%H:%M:%S}\n{sys.executable=}\n{PATH=}\n{traceback.format_exc()}\n"
        )
