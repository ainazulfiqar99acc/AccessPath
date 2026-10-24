# Evaluation

All measurements below are from the local implementation on 24 October 2026. Inputs are the three included fictional forms and explicitly synthetic demonstration answers. These are developer checks, not a user study or accessibility certification.

## Real open-weight inference

`python -m scripts.evaluate` ran fresh sequential inference with `qwen3:8b`, Q4_K_M, 8.2B parameters, Apache 2.0 weights. Ollama version: 0.40.8. Hardware: NVIDIA RTX 4090, 24 GB VRAM, shared with other sessions. No shared service configuration or model loading policy was changed.

Model digest: `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.

| Fictional source | Actual fields | Required flags | Conditional fields | Checklist items | Fresh inference wall time |
|---|---:|---:|---:|---:|---:|
| Scholarship | 8 | 7 | 1 | 2 | 3.33 s |
| Community workshop | 5 | 4 | 0 | 1 | 2.00 s |
| Household support | 5 | 5 | 0 | 1 | 1.99 s |

`docs/evaluation-results.json` contains timestamps, source hashes, generated wording, model digest, token counts, and timing. `docs/model-evaluation.json` preserves an earlier successful uncached scholarship run (3.41 s, 371 generated tokens). Timings include the HTTP request and validation; models were already available locally, so these are not cold-start claims. Latency varies with hardware and concurrent sessions.

The parser extracted all 18 manually specified field IDs in exact DOM order. This fixed-fixture check does not estimate performance on unseen websites. Each output covered exactly the source field IDs, and passed the field-specific new-number and selected-claim guards. That result is not a measurement of complete semantic correctness. Human inspection of the recorded scholarship output found its short labels useful and its explicit limits consistent with the source; no independent evaluator or recruited user study was conducted.

The initial number guard rejected a valid `120`-character email limit because it checked only prose. That limit was present in the source `maxlength` attribute. The guard now includes parsed constraints as evidence. This was a validation bug corrected during development, not a fabricated benchmark success.

## Functional checks

Backend tests cover exact extraction, required/optional flags, conditional funding details, email/pattern/length/number/boolean constraints, unknown fields, checklist gates, missing/false/stale/replayed consent, consent expiry, source changes, failure state, value-free audit, origin rejection, and deletion. Consent unit tests stub only the browser boundary; they do not claim to be end-to-end model tests.

Browser tests exercise the running frontend, API, and actual separate portal. The scholarship journey includes genuine local Qwen explanations, the conditional sponsorship field, review, disabled-until-consent submission, a real Playwright receipt, audit, and deletion. The community journey is completed by keyboard, including optional input, save/reload/resume, consent, and actual portal submission. A third journey submits the household form through the real API/browser boundary.

The workspace is checked at 1440×1000. The 390×844 mobile layout is checked with large text and high contrast, including a no-horizontal-overflow assertion. Axe WCAG-relevant scans cover workspace, mobile settings, source analysis, wizard, review, outcome, and privacy/activity. Reports live under `test-results/accessibility/` while reproducible tests live under `tests/e2e/`. Initial low-contrast text and a large-text mobile navigation overflow were corrected based on failing checks.

Final verification: **11 backend tests passed**, **4 browser tests passed** (16.5 seconds for the final full browser run), TypeScript checking passed, and the optimized Next.js production build passed. The eight scanned view/configuration combinations had zero reported axe violations for the selected WCAG tags. The final test run also verifies empty-required-field focus/error feedback and deletes every test-created draft. `docs/verification-results.json` preserves the summary. No synthetic drafts remain in the running local database.

The genuine silent demonstration is **114.92 seconds**, **1920×1080**, H.264/yuv420p, approximately 2.37 MB. FFmpeg decoded the complete recording without errors. Metadata is preserved in `docs/video-evidence.json`.

The completed narrated version uses the user's selected Liam voice and is **114.92 seconds**, **1920×1080**, approximately 4.49 MB. Audio and video track durations match. All 29 subtitle cues are ordered, non-overlapping, and cover the spoken script exactly; there are no punctuation-only cues. The full final MP4 decoded without errors. Final audio measured **-16.16 LUFS**, with **-1.43 dBTP** true peak and zero clipped PCM samples. Caption layout was visually inspected on representative frames, with captions kept below the actual app screen. See `demo/assets/audio/final-verification.json` and [voiceover notes](VOICEOVER.md). No voice-tool name appears in the narration or captions. The [public source repository](https://github.com/ainazulfiqar99acc/AccessPath) and its screenshot assets are published; YouTube upload remains pending.

## Payoff and limits

The demonstrated improvement is structural: a source form with 8 fields becomes one active question at a time, with source evidence and a single confirmation boundary. The conditional field is shown only when relevant. No claim of minutes saved, completion-rate improvement, reduced errors for real applicants, or usability testing with disabled people is supported by this evaluation.

Automated accessibility scans do not certify WCAG 2.2 AA. AI paraphrases can still be wrong. Supported adapters are deliberately limited to the included local forms. Audio interaction, real-agency adapters, automatic crash reconciliation, database encryption, and multi-user authentication remain unimplemented.
