import os
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from .parser import active

PORTAL_URL = os.environ.get('PORTAL_URL', 'http://127.0.0.1:9314').rstrip('/')
if urlparse(PORTAL_URL).hostname not in ('127.0.0.1', 'localhost', '::1'):
    raise RuntimeError('Portal automation must remain on loopback.')


async def fill_and_submit(form, answers):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(service_workers='block')
            async def allow_local(route):
                target = urlparse(route.request.url)
                base = urlparse(PORTAL_URL)
                if (target.scheme, target.netloc) != (base.scheme, base.netloc):
                    await route.abort()
                else:
                    await route.continue_()
            await context.route('**/*', allow_local)
            page = await context.new_page()
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
