import hashlib
import json
import os
import secrets
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from . import ai, automation
from .parser import FORM_IDS, parse_form, validate_answers, active
from .schema import CreateSession, UserAnswer, ProposedAction
from .storage import db, event, now, session, public_session

app = FastAPI(title='AccessPath local API', version='0.1.0')
ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://127.0.0.1:3103')


@app.middleware('http')
async def privacy_headers(request: Request, call_next):
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        if request.headers.get('origin') not in (None, ORIGIN):
            return JSONResponse({'detail': 'This action must come from the local AccessPath app.'}, status_code=403)
        if int(request.headers.get('content-length', '0')) > 30000:
            return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


def checked_form(row):
    form = parse_form(row['form_id'])
    if row['source_hash'] != form.source_hash:
        raise HTTPException(409, 'The source form changed. Start a new draft to review its requirements.')
    return form


@app.get('/api/health')
async def health():
    return {'status': 'ok', 'model': await ai.model_status(), 'portal_url': automation.PORTAL_URL}


@app.get('/api/forms')
def forms():
    return [parse_form(f) for f in FORM_IDS]


@app.post('/api/forms/{form_id}/explain')
async def explain(form_id: str):
    if form_id not in FORM_IDS:
        raise HTTPException(404, 'Unsupported fictional form.')
    return await ai.explain(parse_form(form_id))


@app.post('/api/sessions')
def create(payload: CreateSession):
    form = parse_form(payload.form_id)
    identifier = secrets.token_urlsafe(32)
    with db() as con:
        con.execute('INSERT INTO sessions(id,form_id,source_hash,created_at,updated_at) VALUES(?,?,?,?,?)',
                    (identifier, form.id, form.source_hash, now(), now()))
        event(con, identifier, 'draft_created', f'Supported fictional form: {form.id}.')
        return public_session(session(con, identifier))


@app.get('/api/sessions/{identifier}')
def get_session(identifier: str):
    with db() as con:
        row = session(con, identifier)
        checked_form(row)
        result = public_session(row)
        result['events'] = [dict(r) for r in con.execute('SELECT event,created_at,detail FROM events WHERE session_id=? ORDER BY id', (identifier,))]
        return result


@app.put('/api/sessions/{identifier}/answers')
def save(identifier: str, payload: UserAnswer):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = session(con, identifier)
        if row['status'] in ('submitting', 'submitted'):
            raise HTTPException(409, 'This draft is already being submitted or completed.')
        form = checked_form(row)
        unknown = payload.answers.keys() - {f.id for f in form.fields}
        if unknown or any(isinstance(v, str) and len(v) > 2000 for v in payload.answers.values()):
            raise HTTPException(422, 'Unsupported field or value too long.')
        if set(payload.checklist) - {r.id for r in form.requirements}:
            raise HTTPException(422, 'Unsupported checklist item.')
        # Drafts can retain incomplete inputs. Final validation runs before review and submission.
        cleaned = {f.id: payload.answers[f.id] for f in form.fields if f.id in payload.answers and active(f, payload.answers)}
        con.execute("UPDATE sessions SET answers=?,checklist=?,step=?,revision=revision+1,status='draft',token=NULL,token_at=NULL,updated_at=? WHERE id=?",
                    (json.dumps(cleaned), json.dumps(payload.checklist), payload.step, now(), identifier))
        event(con, identifier, 'draft_saved', 'Answers saved locally; previous confirmation invalidated. Values omitted from audit.')
        return public_session(session(con, identifier))


@app.post('/api/sessions/{identifier}/prepare')
def prepare(identifier: str):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = session(con, identifier)
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
                'destination': f'{automation.PORTAL_URL}/forms/{form.id}', 'field_count': len([f for f in form.fields if active(f, answers)])}


@app.post('/api/sessions/{identifier}/submit')
async def submit(identifier: str, payload: ProposedAction):
    if payload.confirmation is not True:
        raise HTTPException(403, 'Explicit confirmation is required.')
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = session(con, identifier)
        digest = hashlib.sha256(payload.action_token.encode()).hexdigest()
        if row['status'] != 'review' or not row['token'] or not secrets.compare_digest(digest, row['token']) or time.time() - (row['token_at'] or 0) > 600:
            raise HTTPException(409, 'Review this draft again before confirming. Confirmation expires after 10 minutes or any edit.')
        form = checked_form(row)
        answers = json.loads(row['answers'])
        if validate_answers(form, answers):
            raise HTTPException(422, 'The reviewed answers are no longer valid.')
        con.execute("UPDATE sessions SET status='submitting',token=NULL,token_at=NULL WHERE id=?", (identifier,))
        event(con, identifier, 'submission_confirmed', 'User explicitly confirmed filling and submitting the fictional local portal.')
    try:
        receipt = await automation.fill_and_submit(form, answers)
    except Exception:
        with db() as con:
            con.execute("UPDATE sessions SET status='draft' WHERE id=?", (identifier,))
            event(con, identifier, 'automation_failed', 'Local portal automation did not return a verified receipt. No automatic retry.')
        raise HTTPException(502, 'The local portal did not return a receipt. Review before retrying; no automatic retry was made.')
    with db() as con:
        con.execute("UPDATE sessions SET status='submitted',receipt=?,updated_at=? WHERE id=?", (receipt, now(), identifier))
        event(con, identifier, 'portal_received', 'Fictional portal returned a receipt. No personal values retained by portal.')
        return public_session(session(con, identifier))


@app.delete('/api/sessions/{identifier}')
def delete(identifier: str):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = session(con, identifier)
        if row['status'] == 'submitting':
            raise HTTPException(409, 'Wait for the active local submission to finish, then delete.')
        con.execute('DELETE FROM events WHERE session_id=?', (identifier,))
        con.execute('DELETE FROM sessions WHERE id=?', (identifier,))
    return {'deleted': True}
