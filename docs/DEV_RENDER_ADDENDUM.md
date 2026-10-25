> REVIEW DRAFT — Render deployment is not yet authorized or verified. Do not append this draft to the published post as a completed integration. No deployed link or Render prize-category claim has been invented.

## Render deployment update

The original AccessPath demo runs locally. The Render upgrade prepares the same Next.js interface as a static export, FastAPI API and fictional portals for one container, so visitors can try the guidance without installing the local stack. The purpose is to host the functional form journey, including a real confirmed browser submission, rather than a static promotional page.

The deployment design preserves a useful boundary: only the Python gateway faces the internet; it serves the Next.js frontend and delegates to the existing API. The API and fictional portal stay on loopback inside the container. Playwright still submits only the current fictional portal; its allowlist was narrowed to the form and required assets rather than opened to real websites.

The privacy tradeoff is explicit. In hosted mode, synthetic draft answers live temporarily on Render. Fictional form instructions go to Groq and its selected open-weight Qwen 3.8 27B model. Answers are not included in model requests. Visitors see a prominent Synthetic Demo notice and use supplied sample text. Browser cookies isolate drafts, which expire within two hours and can be deleted immediately.

The implementation includes a Docker image definition, Render Blueprint, supervised processes, runtime-secret configuration, production health checks, request deadlines, bounded anonymous-demo usage, and deployment-specific browser tests. The local Ollama workflow remains supported. A real Groq call has been checked locally; the actual deployed journey and 512 MB runtime still need verification before claiming the Render integration complete.

Before this addendum is finalized, verify the real public URL and hosted inference, run the public end-to-end and accessibility checks, capture actual Render screenshots and a narrated recording, and update the original article's local-only/privacy descriptions. Include the actual verified URL and media at that point. Add **Best Use of Render** to a final Prize Categories section only after the working integration is verified and the user reviews the post update.
