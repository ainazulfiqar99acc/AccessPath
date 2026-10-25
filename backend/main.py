import hashlib
import json
import sqlite3
import secrets
import time
import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from . import ai, automation
from .parser import FORM_IDS, parse_form, validate_answers, active
from .schema import CreateSession, UserAnswer, ProposedAction
from .storage import db, event, now, session, public_session, purge_expired
from .config import settings, validate_startup
from .demo import SAMPLES, validate_synthetic
from .security import BodyLimitMiddleware, browser_identity, consume_limit

@asynccontextmanager
async def lifespan(app):
    validate_startup()
    with db() as con:
        purge_expired(con)
    async def cleanup():
        while True:
            await asyncio.sleep(60)
            with db() as con:
                purge_expired(con)
    task = asyncio.create_task(cleanup())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title='AccessPath API', version='0.2.0', lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(BodyLimitMiddleware)


@app.middleware('http')
async def privacy_headers(request: Request, call_next):
    config = settings()
    request.state.config = config
    name, value, owner, fresh = browser_identity(request, config.hosted)
    request.state.owner_hash = owner
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        allowed = (config.origin,) if config.hosted else (None, config.origin)
        if request.headers.get('origin') not in allowed:
            return JSONResponse({'detail': 'This action must come from the AccessPath app origin.'}, status_code=403)
    if config.hosted and request.url.path not in ('/api/readyz', '/api/health'):
        try:
            with db() as con:
                purge_expired(con)
                consume_limit(con, 'browser:' + owner, 90, 60)
                consume_limit(con, 'global', 600, 60)
        except HTTPException as exc:
            return JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers=exc.headers)
    response = await call_next(request)
    if fresh and request.url.path != '/api/readyz':
        response.set_cookie(name, value, max_age=86400, secure=config.hosted, httponly=True, samesite='strict', path='/')
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


def owned(con, identifier, request):
    return session(con, identifier, request.state.owner_hash, request.state.config.hosted)


def checked_form(row):
    form = parse_form(row['form_id'])
    if row['source_hash'] != form.source_hash:
        raise HTTPException(409, 'The source form changed. Start a new draft to review its requirements.')
    return form


@app.get('/api/health')
async def health():
    config = settings()
    return {'status': 'ok', 'model': await ai.model_status(), 'portal_url': config.origin if config.hosted else config.portal,
            'deployment': {'mode': config.mode, 'synthetic_only': config.hosted,
                           'draft_ttl_seconds': config.ttl if config.hosted else None,
                           'storage': 'Temporary server storage on Render' if config.hosted else 'SQLite on this device',
                           'inference': 'Groq receives fictional form instructions only' if config.provider == 'groq' else 'Hugging Face and the selected Qwen provider receive fictional form instructions only' if config.provider == 'huggingface' else 'Ollama on this device'}}


@app.get('/api/readyz')
async def ready():
    # Do not perform billable inference as part of periodic Render health checks.
    try:
        with db() as con:
            con.execute('SELECT 1').fetchone()
        async with httpx.AsyncClient(timeout=3, trust_env=False) as client:
            response = await client.get(settings().portal + '/healthz')
            response.raise_for_status()
        return {'status': 'ok', 'database': 'ok', 'fictional_portal': 'ok'}
    except (httpx.HTTPError, OSError, sqlite3.Error):
        raise HTTPException(503, 'The application storage or fictional portal is not ready.')


@app.get('/api/forms')
def forms():
    return [{**parse_form(f).model_dump(), **({'demo_values': SAMPLES[f]} if settings().hosted else {})} for f in FORM_IDS]


@app.post('/api/forms/{form_id}/explain')
async def explain(form_id: str):
    if form_id not in FORM_IDS:
        raise HTTPException(404, 'Unsupported fictional form.')
    return await ai.explain(parse_form(form_id))


@app.post('/api/sessions')
def create(payload: CreateSession, request: Request):
    config = request.state.config
    if config.hosted and not payload.synthetic_ack:
        raise HTTPException(422, 'Confirm that you will use synthetic sample answers only.')
    form = parse_form(payload.form_id)
    identifier = secrets.token_urlsafe(32)
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        if config.hosted:
            purge_expired(con)
            if con.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] >= 200 or con.execute('SELECT COUNT(*) FROM sessions WHERE owner_hash=?', (request.state.owner_hash,)).fetchone()[0] >= 3:
                raise HTTPException(429, 'The demo draft limit was reached. Delete an existing draft or try again after it expires.')
        con.execute('INSERT INTO sessions(id,form_id,source_hash,created_at,updated_at,owner_hash,expires_at) VALUES(?,?,?,?,?,?,?)',
                    (identifier, form.id, form.source_hash, now(), now(), request.state.owner_hash, time.time() + config.ttl if config.hosted else None))
        event(con, identifier, 'draft_created', f'Supported fictional form: {form.id}.')
        return public_session(owned(con, identifier, request))


@app.get('/api/sessions/{identifier}')
def get_session(identifier: str, request: Request):
    with db() as con:
        row = owned(con, identifier, request)
        checked_form(row)
        result = public_session(row)
        result['events'] = [dict(r) for r in con.execute('SELECT event,created_at,detail FROM events WHERE session_id=? ORDER BY id', (identifier,))]
        return result


@app.put('/api/sessions/{identifier}/answers')
def save(identifier: str, payload: UserAnswer, request: Request):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = owned(con, identifier, request)
        if row['status'] in ('submitting', 'submitted'):
            raise HTTPException(409, 'This draft is already being submitted or completed.')
        form = checked_form(row)
        unknown = payload.answers.keys() - {f.id for f in form.fields}
        if unknown or any(isinstance(v, str) and len(v) > 2000 for v in payload.answers.values()):
            raise HTTPException(422, 'Unsupported field or value too long.')
        if set(payload.checklist) - {r.id for r in form.requirements}:
            raise HTTPException(422, 'Unsupported checklist item.')
        if request.state.config.hosted:
            validate_synthetic(form.id, payload.answers)
        # Drafts can retain incomplete inputs. Final validation runs before review and submission.
        cleaned = {f.id: payload.answers[f.id] for f in form.fields if f.id in payload.answers and active(f, payload.answers)}
        con.execute("UPDATE sessions SET answers=?,checklist=?,step=?,revision=revision+1,status='draft',token=NULL,token_at=NULL,updated_at=? WHERE id=?",
                    (json.dumps(cleaned), json.dumps(payload.checklist), payload.step, now(), identifier))
        event(con, identifier, 'draft_saved', 'Answers saved; previous confirmation invalidated. Values omitted from audit.')
        return public_session(owned(con, identifier, request))


@app.post('/api/sessions/{identifier}/prepare')
def prepare(identifier: str, request: Request):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = owned(con, identifier, request)
        if row['expires_at'] and row['expires_at'] - time.time() < 90:
            raise HTTPException(409, 'This demo draft is about to expire. Delete it and start a new form.')
        if row['status'] in ('submitting', 'submitted'):
            raise HTTPException(409, 'This draft has already moved to submission.')
        form = checked_form(row)
        answers = json.loads(row['answers'])
        errors = validate_answers(form, answers)
        if errors:
            raise HTTPException(422, {'message': 'Please check these answers.', 'fields': errors})
        if set(json.loads(row['checklist'])) != {r.id for r in form.requirements}:
            raise HTTPException(422, 'Please confirm each preparation checklist item.')
        token = secrets.token_urlsafe(32)
        con.execute("UPDATE sessions SET token=?, token_at=?,status='review' WHERE id=?", (hashlib.sha256(token.encode()).hexdigest(), time.time(), identifier))
        event(con, identifier, 'review_prepared', 'Requirements validated against source DOM. Awaiting explicit confirmation.')
        return {'action_token': token, 'revision': row['revision'], 'expires_in': 600,
                'destination': f'{request.state.config.origin if request.state.config.hosted else request.state.config.portal}/forms/{form.id}', 'field_count': len([f for f in form.fields if active(f, answers)])}


@app.post('/api/sessions/{identifier}/submit')
async def submit(identifier: str, payload: ProposedAction, request: Request):
    if payload.confirmation is not True:
        raise HTTPException(403, 'Explicit confirmation is required.')
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = owned(con, identifier, request)
        if row['expires_at'] and row['expires_at'] - time.time() < 90:
            raise HTTPException(409, 'This demo draft is about to expire. Start a new form.')
        digest = hashlib.sha256(payload.action_token.encode()).hexdigest()
        if row['status'] != 'review' or not row['token'] or not secrets.compare_digest(digest, row['token']) or time.time() - (row['token_at'] or 0) > 600:
            raise HTTPException(409, 'Review this draft again before confirming. Confirmation expires after 10 minutes or any edit.')
        form = checked_form(row)
        answers = json.loads(row['answers'])
        if request.state.config.hosted:
            validate_synthetic(form.id, answers)
        if validate_answers(form, answers):
            raise HTTPException(422, 'The reviewed answers are no longer valid.')
        if automation.LOCK.locked():
            raise HTTPException(409, 'Another synthetic submission is running. Wait a moment, then confirm again.')
        con.execute("UPDATE sessions SET status='submitting',token=NULL,token_at=NULL WHERE id=?", (identifier,))
        event(con, identifier, 'submission_confirmed', 'User explicitly confirmed filling and submitting the fictional local portal.')
    try:
        receipt = await asyncio.wait_for(automation.fill_and_submit(form, answers), timeout=60)
    except Exception:
        with db() as con:
            con.execute("UPDATE sessions SET status='draft' WHERE id=?", (identifier,))
            event(con, identifier, 'automation_failed', 'Local portal automation did not return a verified receipt. No automatic retry.')
        raise HTTPException(502, 'The fictional portal did not return a receipt. Review before retrying; no automatic retry was made.')
    with db() as con:
        con.execute("UPDATE sessions SET status='submitted',receipt=?,updated_at=? WHERE id=?", (receipt, now(), identifier))
        event(con, identifier, 'portal_received', 'Fictional portal returned a receipt. No personal values retained by portal.')
        return public_session(owned(con, identifier, request))


@app.delete('/api/sessions/{identifier}')
def delete(identifier: str, request: Request):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = owned(con, identifier, request)
        if row['status'] == 'submitting':
            raise HTTPException(409, 'Wait for the active local submission to finish, then delete.')
        con.execute('DELETE FROM events WHERE session_id=?', (identifier,))
        con.execute('DELETE FROM sessions WHERE id=?', (identifier,))
    return {'deleted': True}
