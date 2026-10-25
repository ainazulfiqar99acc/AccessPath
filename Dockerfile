FROM node:22-bookworm-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY app ./app
COPY components ./components
COPY lib ./lib
COPY next.config.ts next-env.d.ts tsconfig.json postcss.config.mjs components.json ./
ENV NEXT_TELEMETRY_DISABLED=1 ACCESSPATH_STATIC_EXPORT=true ACCESSPATH_BUILD_DIR=.next
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright NEXT_TELEMETRY_DISABLED=1 \
    ACCESSPATH_MODE=hosted SYNTHETIC_DEMO=true AI_PROVIDER=groq \
    ACCESSPATH_DATA=/tmp/accesspath PORTAL_URL=http://127.0.0.1:9314 ACCESSPATH_FRONTEND_DIR=/app/frontend
COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 accesspath
COPY --from=frontend --chown=accesspath:accesspath /app/out /app/frontend
COPY --chown=accesspath:accesspath backend /app/backend
COPY --chown=accesspath:accesspath deploy /app/deploy
USER accesspath
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','10000')+'/api/readyz',timeout=4)"
CMD ["python", "-m", "deploy.start"]
