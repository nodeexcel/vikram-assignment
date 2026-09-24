# Single stage on purpose: there is nothing to compile, so a builder stage would
# add moving parts without shrinking the image.
FROM python:3.13-slim

# PYTHONDONTWRITEBYTECODE: no .pyc in a layer that is read-only at runtime.
# PYTHONUNBUFFERED: logs reach the platform's collector immediately rather than
# sitting in a buffer when the container is killed.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first and on their own layer, so editing a fixture or a template
# does not reinstall the world.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Only what the application reads at runtime. The markdown documents are copied
# because /how-it-works and /where-this-goes-next read them from the repo root
# at request time — one copy, not two that drift.
COPY app/ ./app/
COPY fixtures/ ./fixtures/
COPY HOW_IT_WORKS.md WHERE_THIS_GOES_NEXT.md ./

# Non-root. Nothing here writes to disk — proposal responses are held in memory —
# so the application owns nothing and needs no writable mount.
RUN useradd --create-home --uid 10001 lexo && chown -R lexo:lexo /app
USER lexo

# Render supplies PORT and defaults it to 10000; this default is for a bare
# `docker run` with no -e PORT. The server must bind 0.0.0.0, not localhost, or
# the platform cannot route to it.
ENV PORT=8000
EXPOSE 8000

# Local convenience. Render runs its own health check against healthCheckPath
# and ignores this directive.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/health').read()"]

# JSON form so no implicit shell wraps the process, with an explicit sh -c
# because $PORT has to be expanded at runtime. `exec` matters: without it the
# shell stays PID 1 and never forwards SIGTERM, so every container stop and
# every redeploy would hang until the 10s SIGKILL instead of shutting down
# gracefully.
CMD ["sh", "-c", "exec uvicorn app.web.main:app --host 0.0.0.0 --port \"$PORT\""]
