---
name: summarize-learning-videos
description: Convert Bilibili, YouTube, and other accessible learning-video links into detailed, timestamped Chinese study notes and save them as Obsidian-compatible Markdown. Always use this skill when the user includes the standalone alias "SLV" in any letter case (for example, SLV, slv, or Slv) to request work on a video; treat the alias as an explicit invocation of summarize-learning-videos. Also use when the user provides a video URL or local video and asks for a comprehensive summary, structured extraction, study notes, review material, transcript-backed analysis, or export to their Obsidian vault. Handle subtitles, local speech transcription, visual-heavy videos, metadata, source-quality disclosure, and note archiving.
---

# Summarize Learning Videos

Turn accessible videos into complete, traceable learning notes. Prefer source coverage and accuracy over speed. Do not present a page description or another person's summary as if it covered the full video.

## Recognize the SLV alias

Treat the standalone token `SLV`, case-insensitively, as an explicit request to use this skill. When the request includes `SLV` and a video URL or local video, run the complete workflow unless the user explicitly narrows the requested output. When `SLV` is present but no video source is provided, ask for the URL or local video instead of substituting another workflow.

## Load configuration

1. Read the path in `VIDEO_NOTES_CONFIG` when that environment variable is set.
2. Otherwise look for `project-config.yaml` in the current workspace.
3. Use its output path, retention choices, language, and note defaults.
4. If no configuration exists, ask for the Obsidian vault and target folder before the first export. Use `references/project-config.example.yaml` as the schema.
5. Ask only when a required choice is missing or writing would overwrite an existing note.

## Acquire the source

Use this priority order:

1. Author-provided subtitles.
2. Platform-generated subtitles.
3. Local audio transcription with MLX Whisper.
4. Page metadata only as supplementary context, never as a substitute for the video.

Prefer one invocation of `scripts/run_pipeline.py`. It must collect metadata, choose the best subtitle, fall back to audio only when subtitles are unavailable, run the configured MLX Whisper model, normalize timestamps, create a complete chapter-organized reading file, and record stage timings. Pass `--language zh` for clearly Chinese audio; otherwise omit language to allow detection. Add `--cookies-from-browser chrome` only when public access fails and the user has authorized use of their logged-in browser state.

Use `scripts/prepare_video.py`, `scripts/normalize_transcript.py`, and `scripts/chapterize_transcript.py` separately only for recovery or debugging. Do not fetch metadata twice merely to discover that audio is needed.

Preserve the full source coverage in the internal chapter reading file. Keep the source language there; summarize in Chinese unless the user requests another language.

Never bypass DRM, payment, private access controls, or platform permissions. State the limitation when the source cannot be accessed.

## Inspect visual information

Treat the transcript as insufficient when the video relies on slides, diagrams, screen demonstrations, equations, code, product interfaces, or silent visual examples.

For those videos:

1. Inspect representative frames at chapter boundaries and major topic changes.
2. Capture additional frames around phrases such as “看这里”, “如图”, “这个界面”, or “这段代码”.
3. Describe only information visible in the inspected frames.
4. Store retained images under the configured attachment folder and use Obsidian embeds.

## Build the note in two passes

### Pass 1: coverage map

1. Read the complete `chapterized.md`, preferably in one combined read when it fits the context.
2. Divide the video by topic changes rather than fixed time intervals.
3. Map every substantial segment to a chapter.
4. Extract the main claim, explanation, evidence, example, caveat, and conclusion for each chapter.
5. Record names and technical terms that require verification.

### Pass 2: detailed synthesis

1. Follow `references/summary-template.md`.
2. Adapt the structure using `references/video-type-guides.md`.
3. Paraphrase copyrighted content; include only short excerpts when wording itself matters.
4. Separate the creator's claims from established facts and from the summarizer's inference.
5. Preserve important original-language terms in parentheses.
6. Make length proportional to information density, not merely runtime.

## Pass the mandatory quality gate

Treat quality review as a required third pass, not an optional final glance.

1. Draft the note in the temporary work area before final Obsidian export.
2. Re-read the complete `chapterized.md` and the finished draft side by side.
3. Apply every critical item in `references/quality-checklist.md` as pass or fail.
4. Run `scripts/validate_note.py` with the known duration and official chapter count.
5. If any critical semantic or structural item fails, revise the draft and repeat both checks.
6. Export only after the quality gate passes. Then read the exported file back and confirm it matches the approved draft.

Do not waive a failed check to save time. If source limitations make a check impossible, disclose the limitation, lower the source grade where appropriate, and avoid claiming complete coverage.

Do not claim “complete” coverage when:

- the transcript has material gaps;
- the video is visual-heavy but frames were not inspected;
- only metadata, description, or search snippets were available;
- speaker attribution or important terminology remains unreliable.

Include a source-quality statement in every note.

## Optimize without reducing quality

1. Keep the configured `large-v3-turbo` model for subtitle-free videos. Do not switch to a smaller model merely to save time.
2. Use the single-pass pipeline and the complete chapter-organized reading file to reduce tool round trips, not source coverage.
3. Batch uncertain current facts into one primary-source verification pass after building the coverage map.
4. Inspect frames only when visual information is material; do not download full-resolution video for a language-led podcast.
5. Read `timings.json` after each run and report evidence-based bottlenecks. Do not promise a fixed runtime.
6. Never skip chapters, caveats, terminology checks, or final read-back validation for speed.
7. Never skip the mandatory quality gate or its revision loop for speed.

## Save to Obsidian

1. Save the main note in the configured target folder as `<clean video title>.md`.
2. Do not overwrite an existing file without explicit permission. Use a disambiguating suffix when the video is different.
3. Save a cleaned transcript only when configuration requests it; otherwise keep it temporary for analysis and remove it after validation.
4. Use YAML properties, Obsidian `[[wikilinks]]`, tags without `#` in YAML, and relative attachment embeds.
5. Use clickable timestamp links when the platform supports them.
6. Update the configured index note after a successful save; create it on first use if absent.
7. Delete temporary audio and video after successful output unless configuration says otherwise.

Report the saved note path, transcript path if any, source quality, quality-gate result, and any important coverage limitation.
