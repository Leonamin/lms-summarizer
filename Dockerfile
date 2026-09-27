FROM node:24-bookworm-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM debian:bookworm-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.11.25 /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python UV_PYTHON=3.11.15 UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    LMS_DATA_DIR=/data LMS_MODELS_DIR=/models LMS_STATIC_DIR=/app/frontend/dist \
    PATH=/app/.venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl xvfb xauth \
    && curl -fsSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /tmp/chrome.deb \
    && apt-get install -y --no-install-recommends /tmp/chrome.deb \
    && rm /tmp/chrome.deb && rm -rf /var/lib/apt/lists/*
RUN uv python install 3.11.15
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev --extra web \
    && .venv/bin/python -c "import sqlite3; assert sqlite3.sqlite_version_info >= (3,53,0), sqlite3.sqlite_version"
COPY --from=frontend /frontend/dist ./frontend/dist
RUN useradd --uid 10001 --create-home lms \
    && mkdir -p /data /models && chown lms:lms /data /models
USER lms
EXPOSE 8200
ENV LMS_PORT=8200
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8200/api/v1/me', timeout=3)"
CMD ["python", "-m", "src.web"]
