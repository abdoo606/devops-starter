# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY devops ./devops
# Run as a non-root user: the cheapest container hardening there is.
RUN useradd --create-home --shell /usr/sbin/nologin app && chown -R app:app /app
USER app
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-m", "devops.healthcheck", "--disk", "/", "--min-free-mb", "50"]
ENTRYPOINT ["python", "-m", "devops.healthcheck"]
