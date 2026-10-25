# Free Render deployment review

Status: **live and verified** at https://accesspath-demo.onrender.com on Render Free. The user approved the push and public deployment. The actual Linux Docker instance passed readiness, real hosted Qwen, all three public browser journeys, source/consent/portal receipt, isolation/deletion, keyboard and mobile checks. See `render-deployment-evidence.json`.

## Architecture

| Component | Default local mode | Prepared free Render mode |
| --- | --- | --- |
| Next.js / React / TypeScript UI | Existing Node server on loopback 3103 | Same UI built with Next static export; HTML/CSS/JS served by Python |
| FastAPI API | Existing server on loopback 9313 | Existing API dispatched in the public Python ASGI service on `$PORT` |
| Fictional source portal | Loopback 9314 | Private loopback 9314 for automation; same portal routes exposed by the public ASGI gateway for inspection |
| Browser submission | Python Playwright and Chromium | Same fixed selectors and source checks; one browser action at a time |
| Model | Existing local Ollama `qwen3:8b` | Groq's hosted open-weight `qwen/qwen3.8-27b`, Free account limits |
| Drafts | Local SQLite | Temporary SQLite, browser-cookie ownership, maximum two-hour lifetime |

The runtime does not need a Node server. `backend/web.py` serves the actual Next export, delegates `/api` requests to the existing FastAPI application, and delegates source-form paths to the existing portal. API startup validation, expiry, consent checks and privacy middleware run unchanged. Unknown asset paths return 404; sensitive responses are not cached. Fingerprinted Next static assets use immutable caching.

`deploy/start.py` supervises a public Python web process and a separate private portal process. It forwards termination signals only to its own process groups and exits if a child fails. The container runs as an unprivileged user. Only the API/web child receives the inference key. Node is used in the Docker build stage, not at runtime.

The automation allowlist remains private: only the configured HTTP loopback origin, current form, its submit path, CSS and JS are permitted. It never navigates the public domain or real organizations. Downloads, service workers and popup browsing are not used. A single-use reviewed consent capability is consumed before Chromium starts.

## Free plan and limits

The Blueprint specifies `plan: free`, one instance and auto-deploys off. The Hobby workspace subscription is $0; Free web-service compute is also $0 within Render's allowances. No paid database, disk or compute resource is requested. Credits have been excluded at the user's request.

Render Free currently provides 512 MB RAM and 0.1 CPU. It spins down after 15 minutes without inbound traffic and may take about a minute to wake. SQLite contents are lost on spin-down, restart or redeploy. This is a synthetic challenge demo, not a durable or continuously available application. The complete flow passed on Render's actual Linux Free instance. Render's 30-second samples reached about 324 MiB against its approximately 512 MiB limit. This is not a continuous peak measurement or a production load test.

The previously considered Hugging Face router now requires purchased credits for Free accounts, so it is not the default. Its explicitly selected adapter remains optional, with no automatic fallback. The prepared default uses Groq's documented Free tier. Keep the Groq account on Free; do not enable a paid Developer upgrade. Quota exhaustion produces a clear 429 error while original source guidance stays available. No provider account is upgraded by the application.

## Inference and privacy

Groq's current documentation lists `qwen/qwen3.8-27b` with strict JSON Schema output and Free-tier limits. The model author's card identifies Apache 2.0 weights. This differs from the local Qwen3-8B model, and the hosted UI discloses external inference. Only parsed fictional form metadata is sent to the fixed Groq HTTPS endpoint. Answers, browser cookies and consent tokens are not included. Returned field IDs, numbers, length bounds and selected unsupported claims are checked with the existing validators.

A real scholarship request returned checked explanations for all eight fields in 0.99 seconds during preparation. That is a local-to-Groq measurement, not Render latency. The account reported a 1,000-output-token/minute limit; the adapter now requests at most 900 tokens, uses concise labels/explanations, and disables reasoning tokens. Uncached Groq requests are limited to one per minute and 60 per hour in the app; cached source-only results are reusable. Actual provider limits can change.

Hosted synthetic answers are stored on Render, not on the visitor's device. The UI shows a prominent Synthetic Demo notice, requires an acknowledgment and provides fixed sample text through Use sample answer. Text is read-only in hosted mode. Both API and portal reject non-sample text and invalid choices/counts, including during draft saves. Optional text can be left empty or cleared. No application is sent to a real organization.

## Storage and browser isolation

A Secure, HttpOnly, SameSite=Strict, host-only `__Host-accesspath-browser` cookie binds every new draft to its browser. SQLite stores its SHA-256 owner digest; knowing another draft ID is insufficient to read, save, prepare, submit or delete it. Clearing the cookie abandons access until expiry; there is no cross-device login or account recovery.

Hosted drafts expire within two hours regardless of activity; cleanup runs on requests, at startup and every minute. A nearly expired draft cannot begin submission. Limits also include three drafts per browser, 200 per instance, 90 API requests per browser/minute and 600 globally/minute. Request bodies are bounded even without Content-Length. These controls are for a small demo, not comprehensive DDoS protection.

Do not scale this SQLite design beyond one instance. Storage is not application-encrypted. Deletion removes application answers and audit rows, not platform backups or exported artifacts. A crash mid-submission still needs reconciliation; automatic resubmission is absent. Render Free may discard drafts earlier than their stated maximum lifetime.

## Environment and startup

`render.yaml` and `.env.render.example` define the configuration. Render supplies `PORT` and `RENDER_EXTERNAL_URL`. Hosted mode requires an exact HTTPS origin, `SYNTHETIC_DEMO=true`, a selected hosted provider and its runtime key. Mutating requests without the matching Origin are rejected.

- `AI_PROVIDER=groq`, `GROQ_MODEL=qwen/qwen3.8-27b`.
- `GROQ_API_KEY` is a server-only secret declared `sync: false`. Enter it securely in Render; never commit it, use it as a Docker build argument, or place it in a NEXT_PUBLIC variable. Local supplied credentials are encrypted using Windows DPAPI in an ignored tools directory.
- `ACCESSPATH_DATA=/tmp/accesspath`, `DEMO_TTL_SECONDS=7200`.
- `ACCESSPATH_FRONTEND_DIR=/app/frontend` points at the copied Next export.
- `PORTAL_URL=http://127.0.0.1:9314` is fixed for the bundled image. The public origin is never added to the automation allowlist.
- `AI_TIMEOUT_SECONDS=120` gives a total inference deadline. Browser submission has its own 60-second server deadline; the client has bounded request waits.

Startup fails if the export, safeguards, provider configuration or token are missing. `/api/readyz` checks SQLite and the private portal without performing inference. `/api/health` reports storage/provider diagnostics and separates configured credentials from a checked inference observed in the process. Provider errors are sanitized; keys and account error bodies are not forwarded.

## Deployment after approval

1. Review the local diff and approve the GitHub push and public Free-service deployment. For this deployment the user approved both steps, and the existing Free service is now live. Inspect it before creating any additional service.
2. Use the verified Render workspace and check for an existing `accesspath-demo` service before creation. The initial inspection found no matching service.
3. Push the approved configuration to `ainazulfiqar99acc/AccessPath`, then apply `render.yaml` or create an equivalent Docker web service with the Free compute plan. Set the Groq key securely.
4. Wait for the actual Linux build and health check. Record Render's real assigned URL, without guessing it.
5. Run the public checks, confirm actual memory behavior, and keep all resource plans Free. Failures remain explicit; no paid upgrade or simulated response is substituted automatically.

```powershell
# Optional structural validation; creates no resources.
.\.venv\Scripts\python.exe -m pip install -r deploy\requirements-check.txt
.\.venv\Scripts\python.exe -m deploy.validate_blueprint

# Local regression and provider-boundary tests.
.\.venv\Scripts\python.exe -m pytest tests\test_backend.py tests\test_hosted.py -q
npm run typecheck
npm run test:e2e

# After approval, set ACCESSPATH_DEPLOYED_URL to the actual HTTPS Render origin.
npm run test:render
npm run demo:render
```

The Render browser suite covers inference, sample values, original-source comparison, consent, genuine fictional-portal receipt, owner isolation, deletion, keyboard-only save/resume, mobile reflow and selected-rule axe checks. A loopback HTTPS run with real Groq verifies this architecture locally; it is distinct from a run on Render. Optional test doubles in unit tests are never deployment evidence.

The public recorder refuses local/test URLs. It captures actual Render screenshots, source inspection, generated explanations, guided completion, consent, receipt and deletion, then encodes and fully decodes the new recording. It preserves the existing published local demo. A new Liam narration must describe hosted storage/inference accurately; the earlier narration is not reused as a claim that hosted data stays local.

## Public evidence and remaining handoff

Render deployment `dep-dbf128o473hc73bfuqp0` is live from source commit `82d76d8c2d7b20dbc487843df9f05f2f8cecfafe`. Public API checks returned 200, all 18 source fields load, and the checked Groq scholarship explanation is reusable from the source cache. The three public browser tests passed in 48.2 seconds; selected-rule axe scans of analysis, review and mobile/reading-preference views found zero violations. Automated checks are not WCAG certification.

The actual public recording is complete at `demo/assets/render/video/final_demo.mp4`: 91.92 seconds, 1920x1080, Liam narration, 21 exact synchronized captions, matching audio/video durations, zero clipped PCM samples, and full decode passed. Audio measured -16.16 LUFS and -1.35 dBTP. Genuine screenshots and recording/voice evidence are under `demo/assets/render/`. The source explanation in the recording is a checked cache hit from real Groq inference, not a fabricated or manually substituted response.

The earlier local YouTube demo is preserved. A new Render video upload remains a user handoff under `BUILD_PROMPT.md`; no YouTube account is selected or upload performed automatically. The Render addendum and article changes are prepared for review, and the live DEV post has not been edited by the agent.

## Primary references checked 25 October 2026

- [Render Free](https://render.com/docs/free), [compute plans](https://render.com/docs/compute-plans), [pricing](https://render.com/pricing), [Blueprint reference](https://render.com/docs/blueprint-spec), [health checks](https://render.com/docs/health-checks).
- [Groq models](https://console.groq.com/docs/models), [Free limits](https://console.groq.com/docs/rate-limits), [strict structured outputs](https://console.groq.com/docs/structured-outputs), [reasoning controls](https://console.groq.com/docs/reasoning), [billing](https://console.groq.com/docs/billing-faqs), [Qwen model card/license](https://huggingface.co/Qwen/Qwen3.8-27B).
- [Hugging Face's current credit requirements](https://huggingface.co/docs/inference-providers/pricing).
- [Week 3 and Best Use of Render](https://dev.to/challenges/hacktoberfest-week3-2026-10-19). Only a genuinely working deployed integration supports the final category claim.
