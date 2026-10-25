"""Browser ownership, bounded request bodies and shared-instance demo limits."""
import hashlib
import re
import secrets
import time
from fastapi import HTTPException
from fastapi.responses import JSONResponse

COOKIE = '__Host-accesspath-browser'
LOCAL_COOKIE = 'accesspath-browser'


def browser_identity(request, hosted):
    name = COOKIE if hosted else LOCAL_COOKIE
    value = request.cookies.get(name, '')
    fresh = not re.fullmatch(r'[A-Za-z0-9_-]{43}', value)
    if fresh:
        value = secrets.token_urlsafe(32)
    return name, value, hashlib.sha256(value.encode()).hexdigest(), fresh


def consume_limit(con, key: str, limit: int, seconds: int):
    bucket = int(time.time()) // seconds
    stamp = time.time()
    con.execute('DELETE FROM rate_limits WHERE expires_at < ?', (stamp,))
    row = con.execute('SELECT count FROM rate_limits WHERE key=? AND bucket=?', (key, bucket)).fetchone()
    if row and row['count'] >= limit:
        raise HTTPException(429, 'The synthetic demo is busy. Please wait a minute before retrying.', headers={'Retry-After': str(seconds)})
    con.execute('INSERT INTO rate_limits(key,bucket,count,expires_at) VALUES(?,?,1,?) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1',
                (key, bucket, (bucket + 1) * seconds))


class BodyLimitMiddleware:
    def __init__(self, app, limit=30000):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return await self.app(scope, receive, send)
        content_length = dict(scope['headers']).get(b'content-length')
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return await JSONResponse({'detail': 'Invalid content length.'}, status_code=400)(scope, receive, send)
            if size < 0 or size > self.limit:
                return await JSONResponse({'detail': 'Request is too large.'}, status_code=413)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body.extend(message.get('body', b''))
            if len(body) > self.limit:
                return await JSONResponse({'detail': 'Request is too large.'}, status_code=413)(scope, receive, send)
            if not message.get('more_body', False):
                break
        sent = False

        async def bounded_receive():
            nonlocal sent
            if not sent:
                sent = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()

        return await self.app(scope, bounded_receive, send)
