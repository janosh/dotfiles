# Video Compression Script

Re-encode only the primary picture track as HEVC, by default with Apple's hardware VideoToolbox encoder, then use `MP4Box` to swap it back into the original MP4/MOV. Everything else survives: audio, subtitles, chapters, thumbnails, DJI timed metadata (`djmd` gyro/orientation, `dbgi`), creation times, camera tags, user-data boxes, cover images, resolution, displayed frame timestamps, color metadata, HDR metadata (Dolby Vision configuration and per-frame RPUs, mastering display, content light level), plus filesystem times, permissions, ownership, flags and extended attributes.

Each rebuilt file's streams, container and HDR metadata, Dolby Vision RPU count and displayed frame timestamps are verified, and sampled excerpts are scored with VMAF, before it is atomically published. Packets marked for discard by the source edit list are excluded from the timestamp comparison. Omitting those hidden packets can change the header's average frame rate.

Skipped, with the original copied to `--outdir` if given: files this script already compressed (no generation loss on reruns), spatial MV-HEVC video and dual-layer Dolby Vision (the encoders keep only one layer).

## Install

```sh
brew install ffmpeg gpac  # ffmpeg with libvmaf and libx265
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

By default each video gets the smallest file whose three 3 s excerpts all reach VMAF 95 (`--target-vmaf`), found by bisecting the encoder quality on those excerpts. 8-bit sources are encoded as 10-bit Main10 (`--eight-bit` to opt out); 10-bit sources stay 10-bit.

Measured on 6 DJI Mini 4 Pro 4K clips (90 s, 1127 MB) on an M4 Pro, full-clip 4K VMAF:

| Mode | Size | Lowest clip VMAF | Time |
| --- | --- | --- | --- |
| old default, fixed `-q:v 62`, 8-bit | 47.5% | 94.9 | ~35 s |
| `--eight-bit` | 32.8% | 95.7 | 464 s |
| default (10-bit) | 31.6% | 95.2 | 374 s (319 s with `-j 2`) |
| `--encoder x265` | 19.0% | 95.6 | 1069 s |

Per-video targeting removes the overshoot of a fixed quality on easy clips (VMAF 99.9 at q62) while lifting the hardest clip. Picked qualities ranged from 41 to 55 (10-bit), so no single fixed value fits all footage. At equal VMAF, 10-bit VideoToolbox is about 6% smaller than 8-bit at the same speed, and x265 (CPU, preset medium) 25–40% smaller but about 5x slower per encode. A light `hqdn3d` denoise made files larger at equal VMAF, so there is no denoise option.

`--quality N` skips the search and is about 10x faster: VideoToolbox `-q:v` (10-bit needs about 10 less than 8-bit for the same VMAF), or x265 `-crf`. `-j 2` encodes two files at once. `--quality-priority` trades speed for a small quality gain (x265: preset slow). x265 refuses HDR sources, whose metadata it would drop.

Why not HandBrake + ExifTool: HandBrake discards unknown/timed tracks (incl. DJI metadata) that ExifTool cannot restore, and `all:all` can write incompatible tags into the rebuilt container.
