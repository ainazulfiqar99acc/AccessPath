> **REVIEW DRAFT — replacement video link pending.** The supplied YouTube video is verified and embedded below, but it shows the earlier interface. The user requested a complete redesign, and the current project now uses a midnight-blue theme. The refreshed 117.68-second narrated demo is complete locally. Replace the video embed after the user uploads that file; article review and manual DEV publication remain pending.

Title: **The Internet Is Open to Everyone. Filling Out Its Forms Isn't.**

Tags: `devchallenge`, `hf26challenge`, `ai`, `accessibility`.

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

A student finds an education opportunity and opens its application. Before writing about their studies, they have to translate the interface. “Applicant's full legal nomenclature.” “Current matriculation classification.” “Concurrent educational sponsorship declaration.” The questions are ordinary. The language turns them into work.

That student is a fictional protagonist, and the scholarship portal in this project is fictional too. I chose that boundary deliberately: I wanted to build and test an entire accessible form journey without impersonating an agency, sending someone else's application, or implying that an untested tool could navigate every public service.

AccessPath is a local-first accessibility guide for three included forms: a student scholarship application, a community workshop registration, and a household support enquiry. It reads the actual HTML source. A local Qwen model suggests simpler labels and explanations. The original instructions remain beside those suggestions. The user checks preparation items, answers one question at a time, reviews everything, and explicitly decides whether to submit.

There is a working action at the end. After confirmation, a controlled Playwright browser fills the separately served fictional portal, submits its form, and reads the real local receipt. The user can inspect the activity record and delete the saved answers afterward.

The repetitive burden I am trying to reduce is decoding: remembering which phrase means which familiar question, finding the instructions again, and checking whether a field applies. The application makes that information available at the moment it is needed. It also keeps the decision with the person filling the form.

## Demo

The video below demonstrates the working workflow before the visual redesign. The screenshots show the current midnight-blue interface. The refreshed video will replace this embed after upload.

{% youtube bom5s39cFz8 %}

A genuine Playwright recording shows the full scholarship journey using **Synthetic Demo Student** and `student@example.org`. It opens the original portal, shows native validation, requests fresh local Qwen inference, compares explanations with evidence, works through preparation and questions, reviews the answers, confirms submission, reads a receipt, inspects activity, and deletes the draft.

The demonstration is a real browser recording with synthetic inputs and local model inference. The recording and narration scripts are included in the repository, along with measured checks and scene timings. The app runs locally; the README explains how to start its frontend, API, and separate fictional portal.

These are screenshots from the actual application, hosted at verified immutable URLs in the public repository.

The workspace presents three supported fictional forms:

![AccessPath's actual workspace and fictional form picker](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/8870fb6ea96d81bab044f78805321f98d450f6e4/demo/assets/screenshots/hero.png)

The original scholarship portal uses deliberately difficult language:

![The actual fictional scholarship portal before guided completion](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/8870fb6ea96d81bab044f78805321f98d450f6e4/demo/assets/screenshots/original-portal.png)

Local explanations remain beside the source evidence:

![Real Qwen-generated explanations alongside original labels and instructions](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/8870fb6ea96d81bab044f78805321f98d450f6e4/demo/assets/screenshots/processing-evidence.png)

The guided workflow asks one active question at a time:

![The working wizard with an explicitly synthetic student's educational statement](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/8870fb6ea96d81bab044f78805321f98d450f6e4/demo/assets/screenshots/guided-step.png)

Answers are assembled for review before explicit consent:

![The actual final review of synthetic application answers](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/8870fb6ea96d81bab044f78805321f98d450f6e4/demo/assets/screenshots/confirmation.png)

The separate fictional portal returns a real local receipt:

![The verified receipt after the real browser submitted the fictional portal](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/8870fb6ea96d81bab044f78805321f98d450f6e4/demo/assets/screenshots/outcome.png)

The recording uses synthetic details throughout and sends nothing to a real organization.

## Code

The complete source is public at [ainazulfiqar99acc/AccessPath](https://github.com/ainazulfiqar99acc/AccessPath), on the `main` branch, under the MIT license.

The repository includes a reproducible README, dependency locks, MIT license, environment example, architecture guide, measured evaluation results, backend tests, Playwright journeys, axe scans, demonstration recorder, and a publication checklist. Runtime data, credentials, dependency installations, and model weights are excluded.

## How I Built It

The frontend uses Next.js, TypeScript, Tailwind, a shadcn-style Button built on Radix Slot, and native form controls. The backend uses FastAPI, typed Pydantic schemas, BeautifulSoup, and SQLite. Ollama serves `qwen3:8b` locally. The tested model is an 8.2B Q4_K_M build, with Apache 2.0 weights.

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

Fresh inference across the three forms took 3.33, 2.00, and 1.99 seconds respectively on a shared RTX 4090. All 18 expected fields were extracted in order, and each generated explanation passed the implemented guards. These are fixed-fixture measurements on a model already available locally; they are not cold-start benchmarks or estimates for arbitrary websites. The raw generated text, hashes, digest, timing, and counts are preserved in the evaluation JSON.

## Why Does Open Innovation Matter?

A form helper handles information people may not want to send to another service. Open weights made it possible to run the language step on the same device as the application. In this implementation, the model sees only the fictional form instructions. There is no cloud AI fallback and no paid API dependency.

That choice also makes the behavior inspectable. Someone can identify the exact model digest, rerun the evaluation, inspect a generated explanation beside its source, change the model within the supported local Qwen configuration, and improve the guards. The parser, confirmation boundary, browser adapter, and tests are ordinary application code that can be reviewed separately from model output.

The most valuable boundary is that the model is allowed to explain, while deterministic code keeps responsibility for requirements and actions. That separation makes a small open model useful without pretending it is an authority over an applicant's circumstances. It also gives contributors specific places to improve the project: clearer evidence, stronger validation, better keyboard testing, and more honest error recovery.

There is still work to do. The prototype supports only its three fictional forms. A server crash during submission can leave a draft awaiting manual reconciliation. There is no multi-user authentication or encrypted database. Voice interaction and permitted real-site adapters remain future work. Those are reasons to keep the current scope clear and testable.

## The Lazy Payoff

The measured payoff here is not a claim that people finish applications a certain percentage faster. No such study was run.

What the demonstration proves is more specific: eight source fields become one active question at a time; conditional details appear only when relevant; original instructions stay reachable; saved progress survives a reload; and a reviewed action reaches a real fictional portal only after confirmation. The user can then see what happened and remove the saved answers.

The work saved is the work of repeatedly finding, decoding, and holding the form's instructions in mind. The next evaluation should test that claim with consenting participants and measure completion, mistakes, comprehension, and effort. Until then, the project can show the workflow honestly without inventing a human outcome.

A confusing form can make a simple question feel like a test. AccessPath is a small attempt to take some of that test away: a clearer sentence, a manageable step, and enough space to make your own decision.
