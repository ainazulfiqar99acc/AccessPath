import html
import secrets
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from .parser import FORM_DIR, FORM_IDS, parse_form, validate_answers
from .config import settings
from .demo import validate_synthetic
from .security import BodyLimitMiddleware

app = FastAPI(title='Fictional local portals', docs_url=None, redoc_url=None)
app.add_middleware(BodyLimitMiddleware, limit=20000)


@app.get('/healthz')
def health():
    return {'status': 'ok', 'fictional': True}


@app.middleware('http')
async def portal_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'"
    return response


@app.get('/forms/{form_id}', response_class=HTMLResponse)
def form(form_id: str):
    if form_id not in FORM_IDS:
        return HTMLResponse('<h1>Unsupported form</h1>', status_code=404)
    source = (FORM_DIR / f'{form_id}.html').read_text(encoding='utf-8')
    if settings().hosted:
        source = source.replace('<main>', '<main><aside aria-label="Synthetic Demo"><strong>SYNTHETIC DEMO — sample answers only.</strong><p>This is a fictional practice portal hosted on Render. Do not enter personal information. No real organization receives this form.</p></aside>', 1)
    return HTMLResponse(source)


@app.post('/forms/{form_id}/submit', response_class=HTMLResponse)
async def submit(form_id: str, request: Request):
    if form_id not in FORM_IDS:
        return HTMLResponse('<h1>Unsupported form</h1>', status_code=404)
    if int(request.headers.get('content-length', '0')) > 20000:
        return HTMLResponse('<h1>Request too large</h1>', status_code=413)
    values = dict(await request.form())
    if 'declaration' in values:
        values['declaration'] = values['declaration'] == 'on'
    if settings().hosted:
        validate_synthetic(form_id, values)
    errors = validate_answers(parse_form(form_id), values)
    if errors:
        return HTMLResponse('<h1>Check your application</h1><ul>' + ''.join(f'<li>{html.escape(k)}: {html.escape(v)}</li>' for k, v in errors.items()) + '</ul>', status_code=422)
    receipt = 'AP-' + secrets.token_hex(5).upper()
    # The fictional portal retains no applicant values, only returns a receipt.
    return HTMLResponse(f'<!doctype html><html lang="en"><head><title>Fictional confirmation</title><link rel="stylesheet" href="/portal.css"></head><body><main><p>FICTIONAL LOCAL PORTAL</p><h1>Application received</h1><p id="receipt">{receipt}</p><p>No real application was sent. This fictional portal does not retain your form values.</p></main></body></html>')


@app.get('/portal.css')
def styles():
    return Response('body{font:17px Georgia,serif;margin:0;background:#f1f0eb;color:#202a36}header{background:#253b55;color:white;padding:25px;display:flex;justify-content:space-between;gap:20px}main{max-width:740px;margin:40px auto;padding:32px;background:white}label{display:block;margin-top:24px;font-weight:bold}input:not([type=checkbox]),select,textarea{display:block;box-sizing:border-box;width:100%;padding:12px;font:inherit;border:1px solid #6c7681}fieldset{margin:28px 0;border:1px solid #abb1b7;padding:24px}legend{font-weight:bold}p{line-height:1.6}button{padding:16px 24px;background:#253b55;color:white;font:inherit;cursor:pointer}.declaration{display:flex;gap:12px;margin-bottom:24px}:focus-visible{outline:3px solid #be6500;outline-offset:3px}[hidden]{display:none!important}', media_type='text/css')


@app.get('/portal.js')
def script():
    return Response("function update(){document.querySelectorAll('[data-conditional]').forEach(el=>{const [key,value]=el.dataset.conditional.split(':');const show=document.getElementById(key).value===value;el.hidden=!show;el.querySelectorAll('[data-required-when]').forEach(input=>{input.required=show;input.disabled=!show;});});}document.addEventListener('change',update);update();", media_type='text/javascript')
