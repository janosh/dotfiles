# Video Compression Script

Re-encode only the primary picture track as HEVC with Apple's hardware VideoToolbox encoder, then use `MP4Box` to swap it back into the original MP4. Everything else survives: audio, subtitles, chapters, thumbnails, DJI timed metadata (`djmd` gyro/orientation, `dbgi`), creation times, camera tags, user-data boxes, cover images, resolution, displayed frame timestamps, pixel format, color metadata, plus filesystem times, permissions, ownership, flags and extended attributes.

Each rebuilt file's streams, container metadata and displayed frame timestamps are verified before it is atomically published, then filesystem metadata is copied over. Packets marked for discard by the source edit list are excluded from the timestamp comparison. Omitting those hidden packets can change the header's average frame rate.

## Install

```sh
brew install ffmpeg gpac
xcode-select --install  # GetFileInfo/SetFile, to restore creation dates
```

## Usage

```sh
uv run --no-project ~/dev/dotfiles/scripts/compress_videos.py input/*.MP4 # writes input/*-compressed.MP4
uv run --no-project ~/dev/dotfiles/scripts/compress_videos.py input/*.MP4 --outdir ~/Movies/compressed # keeps basenames
```

Existing outputs are kept unless `--overwrite` is passed.

Re-encodes that save less than 10% are rejected. With `--outdir` the original is copied there instead, so the output directory stays complete. With a suffix nothing is written, since the original already sits next to it.

## Quality and speed

Default: `--quality 62` in speed-priority mode. On an M4 Pro with DJI Mini 4 Pro 4K/29.97 HEVC footage this encoded at 3.3–3.4x real-time, scored 96.8–99.9 VMAF, and shrank representative daylight clips by 42–44%.

Savings vary with noise and scene complexity. Use `--quality 64` or `--quality-priority` for safer quality, `--quality 60` when size matters more. Test representative scenes before large batches: two quality points can materially change file size.

Why not HandBrake + ExifTool: HandBrake discards unknown/timed tracks (incl. DJI metadata) that ExifTool cannot restore, and `all:all` can write incompatible tags into the rebuilt container.
