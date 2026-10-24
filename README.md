# AccessPath

**Forms, made clearer. One step at a time.**

AccessPath turns three deliberately confusing, **fictional local forms** into an accessible guided workflow. It reads actual HTML evidence, uses a local Qwen model to simplify the wording, keeps the originals beside the suggestions, and checks answers against the source constraints. A real Playwright browser fills and submits the fictional portal only after explicit confirmation.

![The actual AccessPath workspace](demo/assets/screenshots/workspace.png)

## Run on Windows

Requirements: Node.js 20.9+, Python 3.12, Ollama, and the `qwen3:8b` model. This implementation was tested with Node 22.14.0, Python 3.12.7, Ollama 0.40.8, and an RTX 4090. The installed Q4_K_M model occupies about 5.2 GB on disk; runtime memory needs additional headroom. CPU inference is supported by Ollama but was not benchmarked here.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
npm ci
.\.venv\Scripts\python.exe -m playwright install chromium
npx playwright install chromium
ollama pull qwen3:8b
.\scripts\start.ps1
```

Open **http://127.0.0.1:3103**. The API uses **9313**, and the fictional portal uses **9314**. All three services bind to loopback. The start script refuses occupied ports and never stops another project. Logs and this project's process IDs are in `logs/`. Run `ollama serve` separately if Ollama is not already running; do not start a second Ollama service over an existing one.

To stop only AccessPath, run `.\scripts\stop.ps1`. It verifies project-specific command lines before stopping processes; it does not stop Ollama or other projects. Then use `.\scripts\start.ps1` to restart.

The configuration reads process environment variables. `.env.example` documents them; `.env` files are not automatically loaded. Use the exact `127.0.0.1` frontend URL so the origin check matches. Keep the defaults when running alongside other sessions.

Manual alternative, from the project root in three terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.portal:app --host 127.0.0.1 --port 9314 --no-access-log
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 9313 --no-access-log
npm run dev
```

For production verification without interfering with the running dev server:

```powershell
$env:ACCESSPATH_BUILD_DIR='.next-production'
npm run build
# Stop only this project's dev web process before running on the same port:
npm start
```

Use the same `ACCESSPATH_BUILD_DIR` for build and start. `scripts/start.ps1` starts development mode. A Docker setup is not included: keeping the existing host Ollama and portal strictly on loopback avoids introducing cross-container network exceptions in this initial version.

## Try the real workflow

1. Choose the student scholarship, community workshop, or household support enquiry.
2. Select **Explain this form**. Qwen runs locally; the model receives only the fictional form fields and constraints, never applicant answers. Generated explanations are cached by source hash and model digest.
3. Compare the suggested wording with the original evidence. Ambiguous source instructions remain visible.
4. Confirm the source-derived preparation checklist. No documents are uploaded.
5. Answer one question at a time. Optional fields, conditional funding details, character limits, patterns, and number bounds come from HTML. Continue or save before leaving to preserve edits.
6. Review the full answer summary. The submit button remains disabled until you explicitly check the confirmation box.
7. A controlled browser fills the local portal and returns a fictional receipt. Inspect the activity trail and delete the local draft when finished.

There is one current draft per browser. Delete the existing saved form before starting another, so old answers are not silently abandoned. A successful submission stays readable until deletion. On reload, **Resume form** reopens source review; your saved question position is retained. AI wording can be loaded again from the source-version cache.

## What is implemented

- Next.js App Router, TypeScript, Tailwind v4, a shadcn-style Button built with Radix Slot, and native accessible form controls.
- FastAPI and typed Pydantic models, real BeautifulSoup DOM extraction, SQLite local drafts and value-free audit events.
- Real `qwen3:8b` structured inference through local Ollama, field/number/selected-claim guards, source-version caching, clear offline/error states, one inference at a time within this API process.
- Three separately served fictional HTML portals with browser and server validation.
- Keyboard navigation, focus management, error announcements, skip link, larger text, high contrast, and reduced-motion support.
- Ten-minute, single-use confirmation capability; any edit invalidates it. The application rechecks the DOM version and answers before automation. External browser requests are blocked.
- Local deletion of answers and audit records, with SQLite secure deletion enabled.

## Tests and evidence

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_backend.py -q
npm run typecheck
npm run test:e2e
.\.venv\Scripts\python.exe -m scripts.evaluate
npm run demo:record
```

Start all services before browser tests or recording. Tests use explicitly synthetic values and delete their own drafts. Backend consent unit tests use an explicitly scoped automation stub; end-to-end tests exercise the real browser and portal. The evaluation script runs fresh real model inference on all three source forms, sequentially, and stores results in `docs/evaluation-results.json`.

See [evaluation details](docs/EVALUATION.md), [architecture](docs/ARCHITECTURE.md), and the [demo script](docs/DEMO_SCRIPT.md). Screenshots are captured from the actual app. `demo/assets/video/demo_silent.mp4` is generated locally and ignored by Git because it is large.

The completed narrated demo is `demo/assets/video/final_demo.mp4`: **114.92 seconds, 1920×1080, Liam's voice, synchronized captions**. Captions occupy a dedicated band below the recorded screen. The video also includes a selectable subtitle track, and the separate SRT is at `demo/assets/audio/subtitles.srt`. See [voiceover reproduction and checks](docs/VOICEOVER.md).

## Privacy and limits

This is a single-user local prototype for the three included fictional forms. It does not automate real agencies, make eligibility decisions, upload documents, or support arbitrary websites. No CAPTCHA or authentication bypass exists. There is no cloud AI fallback and no canned model response.

Draft answers are **not encrypted at rest**. A high-entropy draft identifier in browser localStorage acts as a local capability. Use a trusted private device. Continue/save commits edits; unsaved typing can be lost on a browser refresh. Deletion removes the selected draft and its activity from the app database, not screenshots, videos, operating system backups, or copies you made. The fictional portal returns a receipt without retaining applicant values.

Source-derived constraints are authoritative. Model output checks are structural and partial semantic guards, not a proof of faithful paraphrasing. A model can still make a mistake without triggering them. Browser automation has no tools available to the model; reviewed user input and fixed selectors control it. Automated axe scans cannot certify WCAG 2.2 AA, and no usability study with disabled participants has been conducted.

If the API process crashes mid-submission, a draft can remain `submitting`; no automatic retry occurs. There is currently no in-app crash reconciliation. Inspect this local state before deciding to delete/restart the draft; the fictional portal has no financial or real-world effect. Voice interaction, live-site adapters, authentication, encryption, and robust multi-user operation remain future work.

Qwen3 weights use [Apache 2.0](https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE). [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs) constrain the response schema. App source uses [MIT](LICENSE). Gemma models and the Gemma category are excluded.

## Publication status

The application, genuine screenshots, and narrated video are complete locally. The user selected Liam for narration. GitHub account selection, public repository approval, YouTube handoff, and DEV review remain explicit checkpoints in `BUILD_PROMPT.md`. No account was selected and nothing was published. [Publication checklist](docs/PUBLISHING_CHECKLIST.md) tracks the remaining steps; [DEV draft](docs/DEV_SUBMISSION.md) is marked pending.
