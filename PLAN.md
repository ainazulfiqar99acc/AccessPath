# AccessPath implementation plan

1. Validate local tools/model and reserve project-specific ports (web 3103, API 9313, fictional portal 9314). Do not stop other projects, change shared Ollama configuration, or use global package installs.
2. P0: parse a real fictional scholarship form; generate local Qwen explanations against DOM evidence; guide answers, checklist, local save/resume, review and explicit confirmation; controlled Playwright fills/submits only the local portal; record value-free audit events.
3. Test extraction, constraints, conditional requirements, model output handling, confirmation gates, actual browser completion, keyboard navigation, and axe checks. Run a real model inference and preserve measured results.
4. Extend the same supported adapter to two additional fictional forms, polish responsive and accessibility controls, add local deletion and documentation.
5. Prepare genuine screenshots and a reproducible silent recording. External publishing and final Kokoro voice selection remain user checkpoints from BUILD_PROMPT.md; do not pick accounts or publish automatically.

## Completed locally

- Three working fictional workflows, real Qwen explanations, local save/resume, conditions and validation, review/consent, real browser submission, receipt, audit, and deletion.
- 11 backend tests and 5 end-to-end tests passed. Eight axe configurations report zero selected-rule violations. TypeScript and production build passed.
- Fresh inference recorded for all 18 source fields. Actual screenshots and a 117.68-second 1080p silent demo recorded and decoded successfully.
- README, dependency locks, architecture, evaluation, demo/narration draft, and pending DEV draft prepared. Services remain running on 3103/9313/9314.
- User selected Liam for narration. The final voiceover, 29 timed subtitle cues, and 117.68-second 1080p narrated MP4 are complete and verified. No voice-tool mention appears in the spoken text or captions.
- User approved public GitHub publication under `ainazulfiqar99acc/AccessPath`. Source is pushed to `main`; six immutable public screenshot URLs were verified against local image hashes.
- User requested a full visual redesign: midnight-blue theme, top navigation, horizontal form choices, rebuilt workflow styling, and responsive reading controls. Current screenshots and the 117.68-second narrated recording use that design. The frontend proxy timeout and non-JSON error handling were corrected during re-recording and covered by a regression test.

## Publication completed

The user uploaded the refreshed video at https://youtu.be/VmlFZgN95ro. Playability, embedding, 118-second platform duration, and the current-theme thumbnail were verified. The complete article now embeds that video and verified current screenshots. The user published the article at https://dev.to/zedaina/the-internet-is-open-to-everyone-filling-out-its-forms-isnt-18l5. Public page/API checks verified its body, new video embed, six accessible screenshots, source link, and both required challenge tags. No publication checkpoints remain.

## Render upgrade completed 25 October 2026

- Preserved the existing Next.js frontend, FastAPI logic, source parser, three fictional forms, Qwen/Ollama local mode, source guards, consent state machine and real portal automation.
- Added the Free Render runtime: exported Next.js assets, public Python gateway/API, private loopback portal, Groq Free-tier Qwen, synthetic samples, cookie ownership, expiry, bounded usage and readiness checks.
- Verification: 40 backend tests, five local browser journeys, production/static-export build and TypeScript passed. The actual public Linux deployment passed three further browser journeys including hosted inference, portal receipt, isolation, deletion, keyboard and mobile checks. Public selected-rule axe scans found zero violations.
- User approved push and public Free deployment. Live URL: https://accesspath-demo.onrender.com. The API confirms Free compute and the 512 MiB limit; sampled memory reached about 324 MiB. No paid compute or credit promotion was used.
- Recorded genuine public screenshots and a 91.92-second 1080p demo with Liam narration, 21 exact synchronized captions, matching audio/video durations and full decode passed. New assets are separate from the earlier published local demonstration.
- Remaining user handoffs: upload the new Render video to YouTube, then review/update the existing DEV post using the prepared article/addendum. No automatic YouTube upload or DEV publication.
