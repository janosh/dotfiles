# Video Compression Script

Re-encode video files to H.265 with `HandBrakeCLI` (Apple VideoToolbox) and copy metadata with `exiftool`.

```sh
brew install handbrake exiftool
```

## Tips

If videos are already compressed and originals remain, batch-copy creation times from `input_dir` to `output_dir` (from [this comment](https://github.com/HandBrake/HandBrake/issues/345#issuecomment-689477853)):

```sh
exiftool -all= -tagsfromfile ./input_dir/%f.mp4 -ext mp4 -all:all --matrixstructure -overwrite_original -FileModifyDate ./output_dir
```

For a single video:

```sh
exiftool -tagsFromFile path/to/input.mp4 -extractEmbedded -all:all -FileModifyDate -overwrite_original path/to/output.mp4
```
