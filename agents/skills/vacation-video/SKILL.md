---
name: vacation-video
description: Creates or refines Janosh's vacation films in Final Cut Pro using chronological footage, Mylio photos, handwritten titles, stabilization, adaptive color, and music beneath original sound. Use for vacation or travel video requests in FCP.
---

# Vacation videos

Deliver a finished, editable FCP project and verified movie from a trip name/date. New user instructions override these defaults. Read [fcp-workflow.md](fcp-workflow.md) for native editing, audio, export, and cleanup details.

## Preferences

- **Chronology:** Interleave videos and photos by capture time, correcting camera clocks/timezones. Verify dates and locations from metadata/itinerary; ask only if the trip remains ambiguous. Title the opening trip/date range and subsequent day or location changes.
- **Selection:** Include the best distinct scenery, people, wildlife, and meaningful moments. Reject blurry, grainy, poorly exposed, redundant, or irreparably jerky shots. Follow the requested duration; otherwise, 15–20 minutes is an inferred default for a rich multi-day trip. Never pad or extend by stretching photos.
- **Music:** Warm, positive instrumentals in **major keys (Dur), not minor (Moll)**, with a relaxed pulse. Avoid whimsical/tinkly arrangements, fast rock, sad/heavy orchestration, competing vocals, and artificial nature sounds. Use Bensound “Memories” as the reference; prefer natural acoustic/piano textures over disco synths or lo-fi lounge music. See audition feedback in [fcp-workflow.md](fcp-workflow.md#music-auditions). Prefer licensed free catalog music over Mubert (rejected). Audition before replacing the score; combine compatible tracks to fit. Cut to phrases/beats without breaking chronology or speech. Use **0.3-second cross dissolves** with adequate handles.
- **Original sound:** Preserve speech, birds, streams, waterfalls, and other pleasing ambience. Adjust recordings individually and duck music beneath them; never globally mute or bury camera sound. Distinguish silent footage from disabled audio.
- **Photos:** Use full-resolution Mylio originals for **4.5 seconds** each. Apply smooth, noticeable zoom-ins, roughly **12–16%** as a starting point. Aim toward faces/subjects, preserving all relevant faces, hair, headroom, and important poses/hands. Adjust for framing and resolution.
- **Titles:** Copy the user's earlier native style: **Dakota Regular**, white, **nine seconds**, **105-point location** with **48-point date beneath**. Preserve reference placement/animation; check apparent size, contrast, and face clearance at output resolution. The Sequoia film is the style reference.
- **Color:** Increase contrast/saturation per shot: more for flat/muted footage, less for vivid footage. Account for existing grades; preserve skin tones, highlights, shadows, and natural color without amplifying noise.
- **Motion:** Stabilize jerky time lapses and handheld clips substantially where needed. Watch motion, crop, and warping; don't apply stabilization blindly or judge it from a still.
- **Organization:** Reuse a relevant WIP after checking its actual content/duration; otherwise duplicate the user's empty library template. Final project/movie name: **`<Destination> <Year>`**. Keep one canonical version without “Extended” or “Recovery” clutter; remove obsolete versions only when cleanup is authorized.

## Workflow

1. **Discover:** Inspect FCP libraries/projects, `~/Movies`, mounted media volumes, and `~/Mylio`. Locate the trip, title reference, and template; verify full-resolution media availability. Inventory capture time, orientation, dimensions, duration, audio streams, and representative frames.
2. **Protect:** Export native FCPXML and preserve a recoverable snapshot before structural edits. Keep originals in place. Store project audio as real files inside the `.fcpbundle`, never symlinks to Downloads or temporary assets; verify resolved paths and file types. Use local scratch storage for large intermediates.
3. **Edit:** Apply the preferences above. Preserve source ranges, retiming, identities, and unrelated effects during targeted revisions. Inspect photo endpoints, motion, and speech boundaries as well as contact sheets.
4. **Mix:** Audit the actual used source windows, including nested audio. Set individual levels and smooth music ducks; use an opening fade and roughly **six-second closing music fade**. Listen when supported; otherwise report signal measurements without claiming to have listened.
5. **Finish:** Control FCP through supported computer-use tools. Offline analysis/XML preparation is allowed; never edit FCP databases. Import, resolve warnings, and export fresh native XML to verify retained settings. Wait for analysis/stabilization, then export an MP4 with audio at project resolution/frame rate.
6. **Verify:** Check native timing, photo/title/effect counts and durations, source paths, gains, and keyframes. Decode the whole movie; inspect every shot center, photo endpoint, title, dissolve midpoint, and opening/closing fade. Watch stabilized excerpts and speech passages. Measure loudness/true peak and confirm original sound survived rendering.
7. **Deliver:** After verification and authorized cleanup, Trash superseded projects/exports recoverably and recheck retained media. Verify the library's **Projects smart collection**, leave the final timeline accessible, and provide movie/library/XML links, duration, dependencies, and concise QA/limitations.

## Autonomy and coordination

Infer routine choices; ask only about unresolved trip identity, required account/billing actions, or material artistic uncertainty. Continue independent work while waiting. One agent owns the shared desktop/FCP UI. If parallel agents are authorized, assign separate offline trip directories and explicit file ownership; require handoff before import. This skill does not itself authorize spawning agents.

## References and invocation

If present, inspect `~/Movies/Iceland 2024 - Ambient Journey.fcpbundle` (project `Iceland 2024`, 4K/29.97, 16:44), `~/Movies/Dolomites 2025 - Ambient Journey.fcpbundle` (project `Dolomites 2025`, 1080p/30, 15:47), and the canonical `2022-11-10 Sequoia National Park` library. Do not depend on these trips or the original chat existing.

Example: “Use vacation-video to make my Norway 2025 vacation film.” An explicit duration, such as “make a seven-minute version,” overrides the inferred length default.
