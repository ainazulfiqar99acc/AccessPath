import os
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from .parser import active
from .config import loopback_origin

PORTAL_URL = loopback_origin(os.environ.get('PORTAL_URL', 'http://127.0.0.1:9314'))
LOCK = asyncio.Lock()


async def fill_and_submit(form, answers):
    if LOCK.locked():
        raise RuntimeError('The fictional portal browser is busy.')
    async with LOCK:
        return await _fill_and_submit(form, answers)


def allowed_request(url, form_id):
    target, base = urlparse(url), urlparse(PORTAL_URL)
    return ((target.scheme, target.netloc) == (base.scheme, base.netloc)
            and not target.username and not target.password
            and target.path in (f'/forms/{form_id}', f'/forms/{form_id}/submit', '/portal.css', '/portal.js')
            and not target.query)


async def _fill_and_submit(form, answers):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(service_workers='block', accept_downloads=False)
            context.set_default_timeout(10000)
            context.set_default_navigation_timeout(15000)
            async def allow_local(route):
                if not allowed_request(route.request.url, form.id):
                    await route.abort()
                else:
                    await route.continue_()
            await context.route('**/*', allow_local)
            page = await context.new_page()
            page.on('popup', lambda popup: asyncio.create_task(popup.close()))
            await page.goto(f'{PORTAL_URL}/forms/{form.id}')
            for field in form.fields:
                if not active(field, answers):
                    continue
                value = answers.get(field.id, '')
                if value in ('', False):
                    continue
                element = page.locator(field.evidence.selector)
                if field.type == 'checkbox':
                    await element.check()
                elif field.type == 'select':
                    await element.select_option(str(value))
                else:
                    await element.fill(str(value))
            # This function is called only after the server consumes a reviewed consent token.
            async with page.expect_navigation():
                await page.get_by_role('button').click()
            receipt = await page.locator('#receipt').inner_text(timeout=10000)
            if not receipt.startswith('AP-'):
                raise ValueError('The local portal did not confirm receipt.')
            return receipt
        finally:
            await browser.close()
