# Video Compression Script

Re-encode video files into H265 codec using `handbrakeCLI` (runs hardware-accelerated Apple Videotoolbox encoding) followed by `exiftool` to copy creation time and similar file metadata from source files to re-encoded output files.

Requires `handbrakeCLI` and `exiftool`. `handbrakeCLI` is not on homebrew (as of 2022-07). Download from <https://handbrake.fr/downloads2.php>, mount disk image and move binary therein to a folder on `PATH`:

```sh
sudo cp /Volumes/HandBrakeCLI-1.5.1/HandBrakeCLI /usr/local/bin
```

`exiftool`, a Perl lib for reading and writing EXIF metadata, is on Homebrew:

```sh
brew install exiftool
```

## Tips

Useful command if a set of videos have already been compressed and the originals are still around, meaning they can be used to copy over the correct creation times. This `exiftool` command batch copies metadata from original files in `input_dir` with possibly different file extensions to compressed files in `output_dir`. Adapted from [this GitHub comment](https://github.com/HandBrake/HandBrake/issues/345#issuecomment-689477853).

```sh
exiftool -all= -tagsfromfile ./input_dir/%f.mp4 -ext mp4 -all:all --matrixstructure -overwrite_original -FileModifyDate ./output_dir
```

For a single video, the equivalent command is

```sh
exiftool -tagsFromFile path/to/input.mp4 -extractEmbedded -all:all -FileModifyDate -overwrite_original path/to/output.mp4
```
