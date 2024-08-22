# Mylio's file renaming feature doesn't rename files in chronological order.
# This Python script handles the use case of renaming media files and
# assigning the same new name to the corresponding XMP file if one exists.
# Mylio will auto-detect the new file names.

# Requires Python 3.6+ and expects two command line args: the target directory
# of files to be renamed and the prefix to be inserted in front of the
# sequence counter. It also assumes the files are to be sequenced in
# alphabetical order so best rename the files according to their creation date
# before running this script in Mylio first).

import os
import sys

_, dirname, prefix = sys.argv


os.chdir(dirname)

files = sorted(f for f in os.listdir() if not f.endswith(".xmp"))


print(f"Renaming {len(files)} files along with their XMP files in {dirname} with {prefix =}")


for idx, file in enumerate(files, start=1):
    basename, ext = os.path.splitext(file)
    os.rename(file, f"{prefix}{idx}{ext}")
    if os.path.exists(f"{basename}.xmp"):
        os.rename(f"{basename}.xmp", f"{prefix}{idx}.xmp")
