# Quality checklist

Use this as a release gate. Mark each critical item pass or fail. Revise and repeat when any critical item fails.

## Source grades

- **A**: Complete author-provided subtitle plus any necessary visual inspection.
- **B**: Complete automatic caption with terminology spot checks and any necessary visual inspection.
- **C**: Local ASR covering the full audio, with unclear terms and visual limitations disclosed.
- **D**: Partial transcript, material gaps, or metadata-only access. Never label this a complete summary.

## Coverage

- **Critical:** Confirm transcript end time is close to video duration.
- **Critical:** Account for every substantial chapter or topic segment.
- **Critical:** Identify long gaps, music-only sections, demonstrations, or failed transcription.
- **Critical:** Inspect frames for visual-heavy material.
- **Critical:** Preserve examples, counterexamples, conditions, and closing conclusions.

## Accuracy

- **Critical:** Verify names, products, books, organizations, dates, numbers, and technical terms when uncertain.
- **Critical:** Keep creator claims distinct from verified facts.
- **Critical:** Label inference explicitly.
- **Critical:** Do not invent speaker attribution.
- **Critical:** Do not silently repair an argument by adding facts absent from the source.

## Note quality

- **Critical:** Make the overview understandable without replaying the video.
- **Critical:** Give every major chapter enough explanation to reconstruct its reasoning, not just its conclusion.
- **Critical:** Make timestamp navigation useful and not excessively granular.
- **Critical:** Explain relationships between concepts instead of listing keywords.
- **Critical:** Preserve meaningful speaker disagreement and uncertainty.
- Convert genuine procedures into actionable steps.
- Include limitations and disagreements when they affect application.
- Write review questions that test understanding, not trivia.

## Obsidian safety

- **Critical:** Use a filesystem-safe title and preserve the original title in YAML.
- **Critical:** Leave no template placeholders, TODO markers, or empty required sections.
- Quote YAML strings that contain punctuation.
- Never overwrite an existing note without permission.
- Use relative attachment paths.
- **Critical:** Confirm the final file can be read back after writing.

## Revision loop

1. List failed critical items internally.
2. Return to the exact source chapters related to each failure.
3. Revise with missing reasoning, evidence, attribution, caveats, or navigation.
4. Re-run the semantic checklist and `validate_note.py`.
5. Stop only when all critical items pass or an unavoidable source limitation is explicitly disclosed.
