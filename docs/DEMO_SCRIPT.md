# Reproducible demonstration

All applicant details in this recording are synthetic, visibly named **Synthetic Demo Student**, with the reserved example address `student@example.org`. No real service receives an application.

Start services using `scripts/start.ps1`, confirm local Qwen is ready, then run `npm run demo:record`. The script launches an isolated browser context at 1920×1080. It does not reuse account cookies or the user's browser session. Its Playwright actions use real application controls and real backend/model inference.

1. Workspace: frame the repetitive burden of complex form wording.
2. Fictional original: show the actual long labels and browser validation on an empty submission.
3. Analysis: read the real DOM and request a fresh local Qwen explanation. The recorder clears only this project's source-explanation cache first; no applicant data or other project is affected.
4. Evidence: compare originals and suggested plain labels, with the unresolved review-date ambiguity visible.
5. Preparation: confirm source-derived document readiness; upload no files.
6. Wizard: fill the synthetic student's details, studies, funding answer, educational statement, and declaration.
7. Review: show that sending is disabled before consent, review the summary, then explicitly confirm.
8. Outcome: the API launches its separate controlled browser, fills the actual portal, submits, and reads a real local receipt.
9. Activity/privacy: inspect value-free events and delete the demonstration draft.

The silent MP4 is written to `demo/assets/video/demo_silent.mp4`; raw Playwright WebM is in `demo/assets/video/raw/`. FFmpeg converts to H.264/yuv420p with fast-start metadata. Screenshots are written to `demo/assets/screenshots/`. The recording has deliberate pauses; its exact runtime is measured with FFprobe rather than asserted in advance.

Verified recording: 114.92 seconds at 1920×1080; full FFmpeg decode passed. Absolute path in this workspace: `G:\Hacktoberfest-2026-Week3\03-AccessPath\demo\assets\video\demo_silent.mp4`.

The final narration script is in `demo/assets/audio/narration_script.md`. The user selected Liam. The completed narrated video is `demo/assets/video/final_demo.mp4`, with synchronized speech, burned captions in a separate band, and an additional subtitle track. The spoken text and captions do not mention the voice-generation tool, as requested. `demo/assets/audio/final-verification.json` records the full decode, timing, caption coverage, and audio-level checks. Public hosting and the user-supplied YouTube link remain pending.
