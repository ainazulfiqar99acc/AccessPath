"""Serve the exported Next.js UI and existing API on one low-memory Python process."""
import os
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from .main import app as api
from .portal import app as portal


class WebApplication:
    def __init__(self, directory=None):
        self.directory = Path(directory or os.getenv('ACCESSPATH_FRONTEND_DIR', 'out'))
        self.static = Starlette(routes=[Mount('/', app=StaticFiles(directory=self.directory, html=True, check_dir=False))])

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            if not (self.directory / 'index.html').is_file():
                raise RuntimeError('Exported frontend is missing. Build with ACCESSPATH_STATIC_EXPORT=true first.')
            # Run the existing API startup validation and expiry task once, unchanged.
            return await api(scope, receive, send)
        path = scope.get('path', '')
        api_route = path == '/api' or path.startswith('/api/')
        portal_route = path.startswith('/forms/') or path in ('/portal.css', '/portal.js')
        target = api if api_route else portal if portal_route else self.static

        async def secure_send(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                existing = {name.lower() for name, _ in headers}
                for name, value in [(b'referrer-policy', b'no-referrer'), (b'x-content-type-options', b'nosniff'), (b'x-frame-options', b'DENY')]:
                    if name not in existing:
                        headers.append((name, value))
                if b'cache-control' not in existing:
                    value = b'public, max-age=31536000, immutable' if path.startswith('/_next/static/') and message['status'] == 200 else b'no-store'
                    headers.append((b'cache-control', value))
                message = {**message, 'headers': headers}
            await send(message)

        await target(scope, receive, secure_send)


app = WebApplication()
