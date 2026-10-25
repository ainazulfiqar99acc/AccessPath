> REVIEW COPY — the Render deployment and public screenshots are verified. Insert the update below under **How I Built It**, then append **Prize Categories** after the existing final section. A new 91.92-second narrated Render recording is complete locally; its YouTube upload remains a user handoff. The existing YouTube video shows the earlier local version. The live DEV post has not been changed by the agent.

### Render update: try the complete hosted journey

[Open the live AccessPath Synthetic Demo](https://accesspath-demo.onrender.com). Render hosts the functional application: form selection, parsed evidence, checked AI explanations, guided answers, explicit confirmation, an actual browser submission to the fictional portal, and its receipt. Use the supplied sample answers only.

The deployment uses one Docker web service on Render Free. Next.js builds the existing React interface as a static export. A Python ASGI gateway serves those assets and dispatches requests to the existing FastAPI API. Removing the Node server from the runtime reduces memory use without replacing the application with a promotional page. A separate fictional portal process remains on loopback for automation.

Public source-form inspection goes through the gateway. The submission browser still allows only the private portal origin, the current form's paths and its required assets. It has no account cookies and cannot visit real scholarship or government websites. The source parser, validation, conditional questions and single-use consent boundary remain authoritative.

The hosted model is Groq's open-weight Qwen 3.8 27B, using strict JSON Schema output and the same post-generation guards. Only fictional source metadata goes to Groq. The local version still uses Ollama/Qwen3-8B; the hosted provider is an explicit choice, with no automatic paid fallback. Free quota is finite, so checked source-only explanations are cached and rate-limit errors leave the original guidance available.

Hosting changes the privacy boundary. Synthetic answers are stored temporarily on Render, not on the visitor's device. A secure HttpOnly browser cookie binds every draft to its owner; knowing another draft ID does not grant access. The public wizard supplies fixed sample text, and the API and portal reject arbitrary text, invalid choices and out-of-range counts. Optional text can still be left empty. Drafts expire within two hours and can be deleted immediately; free-service sleep or restarts may remove them sooner.

The actual Linux deployment passed all three public Playwright journeys: scholarship explanation through receipt and deletion, keyboard-only community completion with save/resume, and mobile reading preferences/source inspection. The tests also checked cross-browser draft isolation and a disabled submit button before consent. Three selected-rule axe scans reported zero violations; they are not accessibility certification. The expanded backend suite has 40 passing tests, alongside the five original local browser journeys.

Render reports a roughly 512 MiB memory limit. Its 30-second samples reached about 324 MiB during verification and recording. Those samples are not an instantaneous peak or a multi-user load test. The free service can sleep after 15 idle minutes, so the first visit may take time to wake. This remains a synthetic practice tool with temporary storage, rather than a service for real applicants.

The Dockerfile, Free-plan Blueprint, secret-handling reference, readiness checks, deployment-specific browser tests, genuine public screenshots and recording scripts are included in the repository. The model still explains; deterministic application code checks the source and controls the action.

![Actual public Render workspace with the Synthetic Demo notice](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/workspace.png)

![Original fictional scholarship portal served by the live Render app](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/original-portal.png)

![Actual hosted Qwen suggestions beside source instructions](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/processing-evidence.png)

![Genuine receipt returned by the private fictional portal on Render](https://raw.githubusercontent.com/ainazulfiqar99acc/AccessPath/023679f886658368868c25a69e07a4751a43a9c4/demo/assets/render/screenshots/outcome.png)

## Prize Categories

**Best Use of Render** — Render hosts the working application, its API, the exported Next.js frontend and the controlled fictional-portal browser runtime. The live demo, actual public screenshots and deployed verification evidence are linked above. The hosted AI step uses Groq; the local Ollama version remains available.
