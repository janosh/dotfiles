"""Rename Mylio media files (and their XMP sidecars) into chronological order.

Mylio's built-in renaming doesn't order files chronologically. This renames media files
and gives the matching XMP file (if any) the same new name; Mylio auto-detects the new
names. Expects two args: the target directory and the prefix to insert before the sequence
counter. Files are sequenced alphabetically, so rename them by creation date in Mylio first.
"""

import os
import sys

_, dirname, prefix = sys.argv
os.chdir(dirname)
files = sorted(name for name in os.listdir() if not name.endswith(".xmp"))
print(f"Renaming {len(files)} files along with their XMP files in {dirname} with {prefix =}")

for idx, file_name in enumerate(files, start=1):
    basename, ext = os.path.splitext(file_name)
    os.rename(file_name, f"{prefix}{idx}{ext}")
    if os.path.isfile(f"{basename}.xmp"):
        os.rename(f"{basename}.xmp", f"{prefix}{idx}.xmp")
