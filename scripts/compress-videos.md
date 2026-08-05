# Video Compression Script

Re-encode only the primary picture track as HEVC with Apple's hardware
VideoToolbox encoder, then use `MP4Box` to swap that track back into the original
MP4 structure. This preserves audio, subtitles, chapters, thumbnails, DJI timed
metadata (`djmd` gyro/orientation and `dbgi`), MP4 creation times, camera tags,
user-data boxes, embedded cover images, resolution, frame rate, pixel format,
color range/metadata, and filesystem creation/access/modification times,
permissions, ownership, flags, and macOS extended attributes.

Before atomically publishing an output file, the script verifies those properties.
Only the encoded video payload and encoder tag are expected to change.

## Install

```sh
brew install ffmpeg gpac
```

## Usage

Write next to each source with the default `-compressed` suffix:

```sh
python ~/dev/dotfiles/scripts/compress_videos.py input/*.MP4
```

Or preserve source basenames in a separate directory:

```sh
python ~/dev/dotfiles/scripts/compress_videos.py input/*.MP4 --outdir output
```

Existing outputs are kept unless `--overwrite` is passed.

## Quality and speed

Default: `--quality 62` with VideoToolbox speed-priority mode. On an M4 Pro with
DJI Mini 4 Pro 4K/29.97 HEVC footage:

- encoding ran at about 3.3–3.4x real-time
- representative normal-detail clips scored 96.8–99.9 VMAF
- full metadata-preserving outputs were 42–44% smaller on representative daylight
  clips

Savings vary with camera noise and scene complexity. Use `--quality 64` or
`--quality-priority` for safer quality, `--quality 60` when size matters more, and
test representative scenes before large batches because two quality points can
materially increase file size.

The old ExifTool-after-HandBrake approach could not restore unknown/timed tracks
HandBrake had discarded, including DJI metadata, and `all:all` could write
incompatible tags into a rebuilt container. Keeping the source container and
replacing only its video track avoids both problems.
