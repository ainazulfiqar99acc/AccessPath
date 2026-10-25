Title: **AccessPath: Clearer Forms, One Question at a Time**

Tags: `devchallenge`, `hf26challenge`, `ai`.

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

A student finds an education opportunity and opens its application. Before writing about their studies, they have to translate the interface. “Applicant's full legal nomenclature.” “Current matriculation classification.” “Concurrent educational sponsorship declaration.” The questions are ordinary. The language turns them into work.

Then comes the quiet repetition: rereading an instruction, checking whether a question applies, scrolling back to find a limit, and worrying that a misunderstood phrase will undo the whole application.

I built **AccessPath** to make that journey easier to follow: a web application that uses open-weight AI to explain difficult form wording, keeps the source instructions visible, and takes the user through one question at a time. The student is a fictional protagonist, and the application demonstrates the complete workflow with fictional forms and synthetic answers.

The working application supports three fictional forms: a student scholarship application, a community workshop registration, and a household support enquiry. It parses their actual HTML, uses Qwen through Groq for plain-language suggestions, and checks answers against source-derived rules. Users review preparation items, complete the active questions, save progress, and explicitly confirm before anything is submitted.

Confirmation leads to a real action. A controlled Playwright browser fills the separate fictional portal, submits the reviewed answers, and reads its receipt. The user can inspect the activity record and delete the draft afterward.

The public app is deliberately a **Synthetic Demo**. It supplies fixed sample answers and rejects arbitrary text at the API and portal boundaries. No real scholarship or government service receives an application. That scope lets someone try the complete journey without entrusting personal information to a prototype.

![AccessPath's live workspace with three fictional forms and the Synthetic Demo notice](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/workspace.png)

## Demo

**[Try AccessPath on Render](https://accesspath-demo.onrender.com)** using the supplied sample answers. The [Free service can sleep after idle time](https://render.com/docs/free), so the first visit may take a little while to wake.

This 92-second narrated recording shows the actual public application:

{% youtube odkNzMn_yWw %}

The journey opens the confusing scholarship portal, compares generated suggestions with source evidence, checks preparation, completes the guided questions, reviews the answers, confirms submission, receives a genuine fictional-portal receipt, and deletes the draft.

All details are synthetic, including **Synthetic Demo Student** and `student@example.org`. The explanation shown in the recording is a checked cache hit created by real Groq inference. The footage uses the working application and its actual browser submission.

The original form makes familiar questions look complicated:

![The actual fictional scholarship portal with its difficult labels](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/original-portal.png)

AccessPath puts the suggested explanation beside the evidence it came from:

![Qwen-generated suggestions alongside original source labels and instructions](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/processing-evidence.png)

Submission stays disabled until the user explicitly consents:

![The review screen with the synthetic answers and confirmation controls](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/confirmation.png)

The outcome is a receipt read from the separate portal:

![The genuine fictional-portal receipt produced by the deployed workflow](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/outcome.png)

## Code

**[GitHub: ainazulfiqar99acc/AccessPath](https://github.com/ainazulfiqar99acc/AccessPath)**

The project is public under the MIT license. The repository includes dependency locks, setup instructions, the Dockerfile and Render Blueprint, architecture documentation, evaluation evidence, backend tests, public Playwright journeys, and recording scripts. Actual screenshots are hosted at immutable commit URLs.

Credentials, runtime databases, model weights, dependency installations, and generated large audio/video files are excluded from Git. Contributors can follow the README to run the application and reproduce its checks.

## How I Built It

### Start with the form's evidence

The interface uses Next.js, TypeScript, Tailwind, a Radix-based Button, and native form controls. FastAPI, Pydantic, BeautifulSoup, and SQLite provide the application backend.

Each fictional portal is an actual HTML form. The parser extracts field IDs, labels, instructions, required flags, options, length constraints, numeric bounds, sections, conditional requirements, preparation items, and ambiguity notes. It also hashes the source. That parsed structure controls validation and browser selectors.

This matters because an explanation can sound reasonable while quietly changing a requirement. AccessPath keeps the original instructions reachable throughout the journey. Document checklists and validation rules come directly from the source.

### Give the model a bounded job

The deployed application uses **Qwen 3.8 27B through Groq**, with strict JSON Schema output. The model receives fictional source metadata. Applicant answers, browser cookies, and confirmation tokens are excluded from the inference request.

Qwen returns plain labels and short explanations. Application guards require its field IDs to match the source and reject numbers absent from that field's prose, options, or HTML attributes. Other filters reject selected unsupported claims about eligibility, deadlines, payment, uploads, and required wording for optional fields.

HTML attributes matter as much as visible prose. For example, an email field can specify `maxlength="120"` without repeating that limit in its instructions. The evidence check includes parsed HTML constraints so that an explanation can reference a genuine limit without inventing one.

The guards still cannot prove every paraphrase faithful. The UI labels AI wording as a suggestion and preserves the source beside it. Checked source-only explanations are cached to conserve the provider's finite quota. Rate-limit errors remain visible, with the original guidance available.

### Keep the action under application control

The wizard follows source order and shows active questions. Answering Yes to other funding reveals its provider question; changing to No removes the inactive detail when saving. Optional workshop notes can stay empty. Numeric answers must satisfy the source bounds.

Before submission, the API validates answers and preparation, then creates a single-use confirmation capability lasting ten minutes. Editing an answer invalidates it. An atomic transaction consumes it before browser automation starts, so replaying the same capability cannot launch another submission.

Playwright receives fixed selectors and reviewed answers. It starts with a clean context and no account cookies. Its request allowlist permits only the private fictional portal origin, the current form's paths, and required assets. The model cannot issue browsing instructions or submit independently.

### Fit the complete workflow on Render Free

Render runs one Docker web service. Next.js builds the React interface as a static export; a Python ASGI gateway serves those files and dispatches API requests to FastAPI. A separate fictional portal process stays on loopback inside the container. Public source inspection goes through the gateway, while submission automation uses that private portal.

This architecture avoids running a Node server alongside Python and Chromium in the roughly 512 MiB Free container. It still hosts the functional interface, API, storage, and browser action together. Readiness checks validate startup configuration, and browser execution has a deadline and a concurrency limit.

During verification and recording, Render's 30-second memory samples reached approximately **324 MiB**. That is a sampled maximum, not an instantaneous peak or evidence of multi-user load capacity. Free hosting also brings cold starts and ephemeral storage. Paid compute and paid inference are never selected automatically.

### Make hosted privacy explicit

Synthetic answers are stored temporarily on Render. A secure HttpOnly cookie binds drafts to the browser that created them; knowing another draft's ID does not grant access. The API enforces ownership for reads, changes, confirmation, submission, and deletion.

Drafts expire within two hours and can be deleted immediately. Sleep or restarts may remove them sooner. Activity descriptions record actions without repeating answer values. The database is not encrypted, and application deletion does not erase separately recorded videos or promise removal from every infrastructure backup.

The hosted model processes source instructions externally through Groq. The app makes that boundary visible. Browser isolation here is not an account system: there is no login or cross-device recovery.

### Test the boundaries and the journey

The backend suite has **40 passing tests** covering extraction, conditions, validation, consent, expiry, replay, source changes, origin restrictions, ownership, synthetic-input enforcement, deletion, provider boundaries, and gateway behavior.

Three Playwright journeys passed against the actual public Linux deployment:

- Scholarship guidance through confirmation, real portal receipt, ownership checks, and deletion.
- Keyboard-only community completion with save/resume and optional notes filled, cleared, and left empty.
- Mobile reading preferences, high contrast, larger text, and source-form inspection.

The public suite completed in **48.2 seconds**. That is test execution time, not a claim about how quickly a person completes an application. Three selected-rule axe scans reported zero violations. These developer checks cannot certify WCAG conformance, and I have not conducted a usability study with disabled participants.

## Why Does Open Innovation Matter?

Open weights make the language layer a component contributors can inspect, run, and change. AccessPath uses [Apache 2.0 Qwen weights](https://huggingface.co/Qwen/Qwen3.8-27B) for explanations. Contributors can examine generated wording beside the source, reproduce the application checks, and investigate how a different supported model affects explanation quality.

Groq makes the public demo practical without requiring visitors to install a model. That convenience has tradeoffs: inference depends on a provider, free quota is limited, and the hosted endpoint does not expose a verifiable weights digest. Open weights alone do not make a hosted service private or independent. The storage and inference boundaries still need to be explained.

The parser, guards, confirmation logic, browser adapter, and tests are open application code. Contributors can improve those parts separately from the model: add evidence checks, challenge a paraphrase, strengthen keyboard navigation, or propose a permitted form adapter.

There are clear limits. Only the three included fictional forms are supported. A crash during submission can require manual reconciliation. Real-site integrations, stronger storage protections, account recovery, and voice interaction need further work. Keeping the current scope small makes those gaps visible and the working behavior reproducible.

## The Lazy Payoff

AccessPath takes over some repetitive handling: locating instructions, presenting the next relevant question, preserving progress, checking source constraints, and transferring reviewed answers into the fictional portal.

The demonstration shows eight source fields becoming one active question at a time. Conditional details appear when needed. The original wording stays reachable. Progress survives a reload within the temporary session, and a confirmed action produces a receipt the user can inspect.

I have not measured a percentage reduction in completion time or cognitive effort. That needs a study with consenting participants, including measurements of mistakes, comprehension, and perceived effort. The evidence here establishes the implemented workflow.

For the Slow and Steady theme, the goal is permission to move at your own pace. Someone should be able to pause, reread, resume, and understand the next question without repeatedly reconstructing the whole form.

A confusing form can make a simple question feel like a test. AccessPath is a small attempt to take some of that test away: a clearer sentence, a manageable step, and enough space to make your own decision.

## Prize Categories

**Best Use of Render** — Render hosts AccessPath's functional frontend, FastAPI backend, temporary draft storage, and controlled browser submission runtime. The [live application](https://accesspath-demo.onrender.com), public deployment tests, genuine screenshots, and recorded receipt demonstrate the integration. Qwen inference is served externally through Groq.
