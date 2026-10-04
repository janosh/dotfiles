# FCP implementation notes

Reference-project settings; confirm current UI/native XML before reuse because effect keys and serialization vary by version.

## Libraries and source safety

- `.fcpbundle` = library. Inventory actual project duration/content through each library's **Projects smart collection**, including other events/snapshots (“Long” once meant a 16-second WIP).
- Native `.fcpxmld` exports usually contain `Info.fcpxml` and external media references, not all originals. Keep dependency paths stable; avoid unnecessary full-movie copies in iCloud-synced Documents.
- **Deleting projects can Trash managed media referenced externally by imported projects** (Iceland: `DJI_0597.mp4`). First compare retained references against the obsolete event's `Original Media`; copy/APFS-clone affected files. After authorized cleanup, recheck every retained path and project inventory; restore missing originals in place and verify FCP.
- Finish renders before moving/deleting media. Never empty Trash during routine cleanup or rename open library bundles. For repairs: preserve a recoverable copy, verify the fixed library, then perform requested cleanup; leave unrelated libraries untouched.

## UI and export

- Follow current computer-use docs; refresh AX/DOM after actions. Rename through the browser project's **display name** field, then Return; image → Return can open the timeline, where typing fires editing shortcuts.
- Before sharing, explicitly select the browser project (possibly different from the open timeline); verify export-dialog name/runtime. Observed: **Cmd-E** Export File, **Cmd-9** Background Tasks; Computer, H.264, explicit project resolution, AAC, Rec.709. Verify current shortcuts/settings.
- Select the destination library before File → Import → XML. If paste stalls, use Go to Folder's settable path field. Check Replace's library; correct wrong destinations with Undo Import XML. Avoid Keep Both duplicates.
- Resolve warnings before rendering. “Preparing media for share” can precede a delayed stabilization warning; wait for analysis. For stale warnings on unchanged, previously analyzed effects, compare stabilization with the prior good render before trusting Continue.
- Soundtrack-only changes: export FCP's full mix as Audio Only/WAV, then mux with the verified movie using video stream copy. Preserve metadata/chapters; verify identical video-stream hashes and unchanged timing before replacement.
- Freezes: preserve exports/native XML; confirm no active render/analysis. Try normal recovery, then Activity Monitor force-quit/relaunch if needed. Recheck project inventory, media, and timeline integrity; never repair internal databases directly.

## Timing, XML, and effects

- Use rational seconds/whole project frames: 135 frames = **4.5 seconds** at 30 fps, `135135/30000s` = **4.5045 seconds** at 30000/1001 fps; nine-frame dissolves = **0.3/0.3003 seconds**, respectively.
- Shorter photos require rippling downstream spine offsets/sequence/music endpoints and repositioning connected titles. Resolve parent/source-relative offsets; not every `offset` is absolute timeline time. Compare picture timing before/after audio-only revisions.
- Resolve nested `clip`, `video`, `audio`, `asset-clip`, and media/compound sequences before extracting windows/changing gains; top-level asset clips miss recordings.
- Find `FCPXMLv*.dtd` in the app's `Contents/Frameworks/Interchange.framework/Versions/A/Resources/`; validate against the applicable version. A mismatched DTD cannot prove compatibility. Always import/re-export native XML: FCP can silently ignore valid-looking parameters (see Final checks).
- Copy native effects/templates, including required serialized `effectConfig`; invented IDs/keys can import without working. Observed Color Adjustments: Control Range `19` = `0 (SDR)`, Contrast `17`, Saturation `16`. Confirm in fresh XML/rendered samples.
- Stabilization starting point for selected clips: `adjust-stabilization enabled="1" type="inertiaCam"`, Smoothing `107` = `1.5`. Inspect motion, horizon, crop, wobble, endpoints; an enabled node does not prove successful analysis/rendering.

## Ken Burns geometry

- Honor original orientation, especially HEIC. `adjust-crop mode="pan"` uses two `pan-rect` entries for start/end. **All four distances, including left/right, are percentages of original height.** For width W/height H: pixel bounds `(left×H/100, top×H/100, W−right×H/100, H−bottom×H/100)`; full crop-unit width `100×W/H`.
- Keep crops inside image bounds at project aspect ratio. Preserve zoom ratio when targeting faces; compose portrait originals deliberately.
- Detection misses shaded/small/profile/occluded faces. Review originals/both endpoints; frame all relevant faces with headroom, preserving full-body gestures where needed, not just the largest face.

## Audio

- Avoid blanket camera attenuation: −22 to −25 dB buried recordings under reference scores. Measure **used source windows**, not whole files: streams, loudness/RMS, peaks, low-frequency energy. Frequency statistics cannot reliably identify speech/birds/water.
- Starting points: meaningful sound **~−23 LUFS**, wind-heavy ambience **−27 to −29 LUFS**, source peaks below **~−5 to −4 dB**. Adjust by listening; don't amplify quiet noise to meet targets.
- Imported FCP gain clamped near +12.0412 dB. Cap planned gain at **+12 dB** and lower music for quiet recordings; if necessary, process/relink a derivative deliberately.
- Aim important original sound **~8–10 dB above local music**, adapting to both sources. Reference-only gains: −3 dB base, often −12 dB ducks, deepest ~−29 to −33 dB. Use the quieter overlapping envelope; **~0.5-second pre-duck / 1-second release**, **~0.25-second source fades** without clipping words.
- Copy native volume automation: working keyframes used `value="-12dB"`, `curve="linear"`. **Omit `interp`: FCP ignored the entire music parameter.** After native re-export, verify keyframe count/times/units/levels and source gains.
- Measure final loudness/true peak; leave headroom. Decoded audio doesn't prove audible camera sound. Without supported audio perception, report measurements/playback honestly; “audio content omitted” is not listening.
- Simple source-plus-score verification: align decoded render/source/music windows by cross-correlation, then fit `render = source × gain + music × gain + DC`. Compare fitted gains with the plan; inspect residual energy. EQ/denoising/compression/retiming/nonlinear processing need another model; poor fit alone doesn't prove missing audio.

## Music auditions

- Approved for both films: **Memories** (preferred), **Sweet**, **Tenderness**, **Photo Album** (usable, a little fast), **Small Joys** (usable, too disco/synth). Other feedback: **Long Night** rejected (lo-fi/elevator, unsuited to nature); **Sunny** too whimsical; **Going Higher** too fast; **Born Of The Sky / Age of Wonder** too sad/heavy.
- Check free-use terms/attribution per track. Prioritize heard user feedback over mood tags/automated key estimates; “major” doesn't guarantee cheerful. For generation, request major-key melodies/relaxed pulse without field recordings; avoid scenery metaphors inviting fake ambience.
- Generate short auditions for style selection or free-tier limits; play through native controls or an authorized local audio player. Distinguish prompted style from heard results and generated tracks from catalog music. Save prompt, track identity/URL, duration, license with selected assets.
- After selection/required access, fit exact film duration with a musical cadence/fade; whole-second controls need frame-accurate finishing. Preserve camera-sound ducking when replacing music.
- Obtain permitted exports before using preview/watermarked tracks. Respect sign-in/payment/terms/upload requirements; never silently subscribe, accept terms, or bypass controls.
- After licensing, prefer `curl`/`wget` for issued links. Save attribution/license per track **and film** (Bensound issued separate codes per video); keep credits beside final exports.

## Final checks

- Compare intended settings with fresh native XML: project name, duration/frame rate, photo/title/effect counts/durations, source ranges, music endpoint, gains/keyframes, all percent-decoded media paths.
- Require Sharing finished, nonzero output, readable ffprobe metadata/streams/runtime, and full ffmpeg video/audio decode. Inspect every scene center, photo endpoint, title, dissolve midpoint, opening/closing fade; watch stabilized clips/speech. Check black frames, missing-media cards, clipping, original-sound contribution. Don't spin-poll or repeat unchanged passing checks.
- Investigate differences before claiming equivalence: shifted frames/crops can cause large pixel errors; stills/file size don't establish motion/sound quality.
- Keep a brief local status file: final paths, duration, dependencies, completed checks, limitations.
