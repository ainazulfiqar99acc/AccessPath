"""Public FastAPI with exported Next.js assets; separate private fictional portal."""
import asyncio
import os
from pathlib import Path
import signal
import sys
from backend.config import validate_startup

ROOT = Path(__file__).resolve().parents[1]


def runtime_environment():
    config = validate_startup()
    if not config.hosted or config.portal != 'http://127.0.0.1:9314':
        raise ValueError('The Render image requires hosted mode and the bundled fictional portal on 127.0.0.1:9314.')
    port = int(os.getenv('PORT', '10000'))
    if not 1024 <= port <= 65535 or port in (9313, 9314):
        raise ValueError('PORT must be an unprivileged port distinct from the private services.')
    if not (ROOT / 'frontend/index.html').is_file():
        raise ValueError('The exported Next.js frontend is missing. Build the Docker image first.')
    environment = dict(os.environ, PORT=str(port), ACCESSPATH_FRONTEND_DIR=str(ROOT/'frontend'))
    return environment


async def main():
    environment = runtime_environment()
    children = []
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    try:
        for module, host, port in [('backend.portal:app', '127.0.0.1', '9314'), ('backend.web:app', '0.0.0.0', environment['PORT'])]:
            child_environment = dict(environment)
            if module == 'backend.portal:app':
                child_environment.pop('HF_TOKEN', None)
                child_environment.pop('GROQ_API_KEY', None)
            children.append(await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'uvicorn', module, '--host', host, '--port', port,
                '--workers', '1', '--no-access-log', '--no-proxy-headers', '--timeout-graceful-shutdown', '10',
                cwd=ROOT, env=child_environment, start_new_session=True))
        tasks = [asyncio.create_task(child.wait()) for child in children]
        tasks.append(asyncio.create_task(stop.wait()))
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        failed = not stop.is_set()
        for task in pending:
            task.cancel()
        if failed:
            raise RuntimeError('An AccessPath service exited. Stopping this instance so Render can recover it.')
    finally:
        # Each group contains only a child started above and its own Chromium descendants.
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for child in children:
            try:
                await asyncio.wait_for(child.wait(), timeout=12)
            except asyncio.TimeoutError:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (ValueError, RuntimeError) as error:
        # Configuration errors contain field names, never secret values or provider bodies.
        print(f'AccessPath startup failed: {error}', file=sys.stderr)
        sys.exit(1)
