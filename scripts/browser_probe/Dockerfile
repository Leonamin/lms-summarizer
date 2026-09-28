# Stage 1 verification image; not the application deployment image.
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl ffmpeg xvfb xauth \
    && curl -fsSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /tmp/chrome.deb \
    && apt-get install -y --no-install-recommends /tmp/chrome.deb \
    && rm -f /tmp/chrome.deb && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir 'playwright==1.56.0' 'requests>=2.32.3' 'python-dotenv>=1.1.0'
RUN useradd --create-home probe
COPY probe.py /probe/probe.py
USER probe
WORKDIR /probe
ENTRYPOINT ["python", "/probe/probe.py"]
