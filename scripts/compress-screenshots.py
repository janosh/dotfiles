import os
import sys
import traceback
from datetime import datetime
from subprocess import CompletedProcess, run

# Use this script by creating a new folder action with 'Folder Actions Setup.app' that
# watches '~/Desktop' (pass inputs as arguments!) and runs this shell script:
#
# source ~/.zshrc # can be omitted if the system python3 is 3.9+
# python3 ~/Repos/macos-setup/scripts/compress-screenshots.py "$@"

# Requires: brew install pngquant zopfli imagemagick

# If folder action doesn't appear to trigger after setup, try toggling
# "Enable Folder Actions" in "Folder Actions Setup.app" or add one of the
# default actions and see if that runs.

home_dir = os.path.expanduser("~")


def shell(cmd: list[str], check: bool = False) -> CompletedProcess[bytes]:
    return run(cmd, capture_output=True, check=check)


for file in sys.argv[1:]:  # first arg is this script's name
    if not file.endswith(".png"):
        continue

    try:
        # set check=False to not raise on non-zero exit code as pngquant returns code
        # 98/99 if processed file is not smaller
        shell(
            "/opt/homebrew/bin/pngquant 32 --skip-if-larger --ext .png --force".split()
            + [file],
            False,
        )

        shell("/opt/homebrew/bin/mogrify -resize '1200>'".split() + [file])

        shell("/opt/homebrew/bin/zopflipng -y".split() + [file, file])

        print(f"{os.path.basename(file)=}")
        os.rename(file, f"{home_dir}/Downloads/{os.path.basename(file)}")

    except Exception:
        with open(f"{home_dir}/Desktop/compress-screenshot.log", "a") as logs:
            now = datetime.now()
            logs.write(f"{now:%H:%M:%S}: {traceback.format_exc()}\n")
