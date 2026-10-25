> **RENDER UPDATE — review copy.** The public Render application and screenshots below are verified. The embedded YouTube video documents the earlier local version. A new 91.92-second narrated Render demo is complete locally and awaits the user's upload URL. The published DEV post has not been edited automatically.

Title: **The Internet Is Open to Everyone. Filling Out Its Forms Isn't.**

Tags: `devchallenge`, `hf26challenge`, `ai`.

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

A student finds an education opportunity and opens its application. Before writing about their studies, they have to translate the interface. “Applicant's full legal nomenclature.” “Current matriculation classification.” “Concurrent educational sponsorship declaration.” The questions are ordinary. The language turns them into work.

That student is a fictional protagonist, and the scholarship portal in this project is fictional too. I chose that boundary deliberately: I wanted to build and test an entire accessible form journey without impersonating an agency, sending someone else's application, or implying that an untested tool could navigate every public service.

AccessPath is a local-first accessibility guide for three included forms: a student scholarship application, a community workshop registration, and a household support enquiry. It reads the actual HTML source. The local version uses Qwen through Ollama; the hosted Synthetic Demo uses open-weight Qwen through Groq to suggest simpler labels and explanations. The original instructions remain beside those suggestions. The user checks preparation items, answers one question at a time, reviews everything, and explicitly decides whether to submit.

There is a working action at the end. After confirmation, a controlled Playwright browser fills the separately served fictional portal, submits its form, and reads the real local receipt. The user can inspect the activity record and delete the saved answers afterward.

The repetitive burden I am trying to reduce is decoding: remembering which phrase means which familiar question, finding the instructions again, and checking whether a field applies. The application makes that information available at the moment it is needed. It also keeps the decision with the person filling the form.

## Demo

[Try the live Render Synthetic Demo](https://accesspath-demo.onrender.com) using the supplied sample answers. The screenshots below show that hosted application.

The 1-minute-58-second video shows the earlier local workflow, with narrated guidance and synchronized captions; its privacy wording applies to the local version.

{% youtube VmlFZgN95ro %}

A genuine Playwright recording shows the full scholarship journey using **Synthetic Demo Student** and `student@example.org`. It opens the original portal, shows native validation, requests local Qwen inference, compares explanations with evidence, works through preparation and questions, reviews the answers, confirms submission, reads a receipt, inspects activity, and deletes the draft.

The demonstration is a real browser recording with synthetic inputs and local model inference. The recording and narration scripts are included in the repository, along with measured checks and scene timings. The app runs locally; the README explains how to start its frontend, API, and separate fictional portal.

These screenshots were captured from the actual public Render application and are hosted at verified immutable URLs in the repository. The hosted recording reuses an explanation cache created by a real Groq inference request.

The workspace presents three supported fictional forms:

![AccessPath's actual workspace and fictional form picker](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/workspace.png)

The original scholarship portal uses deliberately difficult language:

![The actual fictional scholarship portal before guided completion](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/original-portal.png)

Checked hosted explanations remain beside the source evidence:

![Real Qwen-generated explanations alongside original labels and instructions](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/processing-evidence.png)

The guided workflow asks one active question at a time:

![The working wizard with an explicitly synthetic student's educational statement](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/guided-step.png)

Answers are assembled for review before explicit consent:

![The actual final review of synthetic application answers](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/confirmation.png)

The separate fictional portal returns a genuine receipt:

![The verified receipt after the real browser submitted the fictional portal](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/outcome.png)

The recording uses synthetic details throughout and sends nothing to a real organization.

## Code

The complete source is public at [ainazulfiqar99acc/AccessPath](https://github.com/ainazulfiqar99acc/AccessPath), on the `main` branch, under the MIT license.

The repository includes a reproducible README, dependency locks, MIT license, environment example, architecture guide, measured evaluation results, backend tests, Playwright journeys, axe scans, demonstration recorder, and a publication checklist. Runtime data, credentials, dependency installations, and model weights are excluded.

## How I Built It

The frontend uses Next.js, TypeScript, Tailwind, a shadcn-style Button built on Radix Slot, and native form controls. The backend uses FastAPI, typed Pydantic schemas, BeautifulSoup, and SQLite. The local setup uses Ollama with `qwen3:8b`, an 8.2B Q4_K_M build with Apache 2.0 weights. The hosted Render setup uses Groq/Qwen 3.8 27B, also open-weight under Apache 2.0; its different storage and inference boundaries are described below.

The starting point is evidence. Each supported portal is a real HTML file served by a separate local app. The parser extracts field IDs, labels, described-by instructions, required flags, select options, length constraints, patterns, numeric bounds, fieldset sections, conditional requirements, preparation items, and ambiguity notes. It also hashes the source. That parsed structure controls validation and browser selectors.

Qwen gets this source metadata, not applicant answers. It returns a structured list of plain labels and short explanations. Its field IDs must match the source exactly. A guard rejects numbers absent from that field's prose, options, and HTML attributes. Additional filters reject selected unsupported claims about eligibility, deadlines, payment, uploads, and required wording for optional fields.

These guards have a narrow job. They catch particular errors; they do not prove that every paraphrase is faithful. The interface therefore preserves the original instructions and says that AI wording is a suggestion. Checklist items and validation rules are extracted directly from the source rather than generated by the model.

One development failure made that distinction especially concrete. Qwen added a 120-character limit to the email explanation. My first guard rejected it because the prose did not mention that number. The actual input did have `maxlength="120"`. The model was right, and the validator was incomplete. I corrected the guard to include parsed HTML constraints. The resulting check is better because of observed evidence, not because every model sentence was assumed correct.

The wizard follows DOM order and displays only active questions. If a scholarship applicant says they receive other funding, the provider question appears. If they change the answer to No, the inactive detail is removed when saving. Optional workshop accommodation notes can be left empty. The household count must be a whole number within the source bounds.

Before submission, the API validates the answers and preparation checklist, then creates a ten-minute confirmation capability. Its digest is stored locally. Editing an answer invalidates it. An atomic transaction consumes it before browser automation starts, preventing a replay from launching a duplicate action. The user still has to check an explicit consent box in the review screen; the submit button starts disabled.

The browser receives fixed selectors and reviewed answers. It does not receive a model-generated browsing plan. It starts with a clean context, has no account cookies, and blocks network requests outside the configured loopback portal origin. It fills the real local form and reads the receipt from the resulting page. The model has no tools that could submit on its own.

SQLite stores drafts on the device. The browser stores a high-entropy draft identifier and reading preferences. Audit descriptions record actions without repeating names, emails, or answers. Deletion removes the draft and its activity from the application database, with SQLite secure deletion enabled. The database is not encrypted, and deletion is not a promise about operating system backups or separately generated video files. Those limits are stated in the interface and README.

Testing covers both logic and actual journeys. Eleven backend tests check extraction, conditions, validation, consent gates, expiry, replay, source changes, browser failure, audit privacy, origin rejection, and deletion. Five browser tests cover the responsive workspace, the scholarship journey with real local inference, keyboard-only community completion with save/resume, household submission through the actual browser boundary, and recovery from a plain-text proxy failure without losing the draft.

Axe scans across eight view/configuration combinations reported no violations for the selected WCAG tags. The redesigned interface uses a horizontal navigation bar, high-contrast blue controls, visible progress, and layouts that reflow with larger text. These developer checks are useful evidence, not WCAG certification. I have not recruited disabled participants or conducted a usability study, so I make no claim that such testing has happened.

In the initial local fixture evaluation, fresh inference across the three forms took 3.33, 2.00, and 1.99 seconds respectively on a shared RTX 4090. All 18 expected fields were extracted in order, and each generated explanation passed the implemented guards. These are fixed-fixture measurements on a model already available locally; they are not cold-start benchmarks or estimates for arbitrary websites. The raw generated text, hashes, digest, timing, and counts are preserved in the evaluation JSON.

### Render update: try the complete hosted journey

[Open the live AccessPath Synthetic Demo](https://accesspath-demo.onrender.com). Render hosts the functional application: form selection, parsed evidence, checked AI explanations, guided answers, explicit confirmation, an actual browser submission to the fictional portal, and its receipt. Use the supplied sample answers only.

The deployment uses one Docker web service on Render Free. Next.js builds the existing React interface as a static export. A Python ASGI gateway serves those assets and dispatches requests to the existing FastAPI API. Removing the Node server from the runtime reduces memory use without replacing the application with a promotional page. A separate fictional portal process remains on loopback for automation.

Public source-form inspection goes through the gateway. The submission browser still allows only the private portal origin, the current form's paths and its required assets. It has no account cookies and cannot visit real scholarship or government websites. The source parser, validation, conditional questions and single-use consent boundary remain authoritative.

The hosted model is Groq's open-weight Qwen 3.8 27B, using strict JSON Schema output and the same post-generation guards. Only fictional source metadata goes to Groq. The local version still uses Ollama/Qwen3-8B; the hosted provider is an explicit choice, with no automatic paid fallback. Free quota is finite, so checked source-only explanations are cached and rate-limit errors leave the original guidance available.

Hosting changes the privacy boundary. Synthetic answers are stored temporarily on Render, not on the visitor's device. A secure HttpOnly browser cookie binds every draft to its owner; knowing another draft ID does not grant access. The public wizard supplies fixed sample text, and the API and portal reject arbitrary text, invalid choices and out-of-range counts. Optional text can still be left empty. Drafts expire within two hours and can be deleted immediately; free-service sleep or restarts may remove them sooner.

The actual Linux deployment passed all three public Playwright journeys: scholarship explanation through receipt and deletion, keyboard-only community completion with save/resume, and mobile reading preferences/source inspection. The tests also checked cross-browser draft isolation and a disabled submit button before consent. Three selected-rule axe scans reported zero violations; they are not accessibility certification. The expanded backend suite has 40 passing tests, alongside the five original local browser journeys.

Render reports a roughly 512 MiB memory limit. Its 30-second samples reached about 324 MiB during verification and recording. Those samples are not an instantaneous peak or a multi-user load test. The free service can sleep after 15 idle minutes, so the first visit may take time to wake. This remains a synthetic practice tool with temporary storage, rather than a service for real applicants.

The Dockerfile, Free-plan Blueprint, secret-handling reference, readiness checks, deployment-specific browser tests, genuine public screenshots and recording scripts are included in the repository. The model still explains; deterministic application code checks the source and controls the action.

## Why Does Open Innovation Matter?

A form helper handles information people may not want to send to another service. Open weights made it possible to run the language step on the same device as the application. Both modes send only fictional source instructions to their model. The default local mode has no cloud fallback or paid API dependency. The hosted demo uses Groq Free-tier inference so visitors can try it without installing the local stack; that external processing and temporary server storage are disclosed explicitly.

That choice also makes the behavior inspectable. For the local model, someone can identify the exact digest and rerun the evaluation. The hosted provider does not expose a verifiable weights digest. A contributor can inspect a generated explanation beside its source, change the model within the supported local Qwen configuration, and improve the guards. The parser, confirmation boundary, browser adapter, and tests are ordinary application code that can be reviewed separately from model output.

The most valuable boundary is that the model is allowed to explain, while deterministic code keeps responsibility for requirements and actions. That separation makes a small open model useful without pretending it is an authority over an applicant's circumstances. It also gives contributors specific places to improve the project: clearer evidence, stronger validation, better keyboard testing, and more honest error recovery.

There is still work to do. The prototype supports only its three fictional forms. A server crash during submission can leave a draft awaiting manual reconciliation. There is no multi-user authentication or encrypted database. Voice interaction and permitted real-site adapters remain future work. Those are reasons to keep the current scope clear and testable.

## The Lazy Payoff

The measured payoff here is not a claim that people finish applications a certain percentage faster. No such study was run.

What the demonstration proves is more specific: eight source fields become one active question at a time; conditional details appear only when relevant; original instructions stay reachable; saved progress survives a reload; and a reviewed action reaches a real fictional portal only after confirmation. The user can then see what happened and remove the saved answers.

The work saved is the work of repeatedly finding, decoding, and holding the form's instructions in mind. The next evaluation should test that claim with consenting participants and measure completion, mistakes, comprehension, and effort. Until then, the project can show the workflow honestly without inventing a human outcome.

A confusing form can make a simple question feel like a test. AccessPath is a small attempt to take some of that test away: a clearer sentence, a manageable step, and enough space to make your own decision.

## Prize Categories

**Best Use of Render** — Render hosts the working application, its API, the exported Next.js frontend and the controlled fictional-portal browser runtime. The live demo, actual public screenshots and deployed verification evidence are linked above. The hosted AI step uses Groq; the local Ollama version remains available.
