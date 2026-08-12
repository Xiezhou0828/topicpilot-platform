FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    UVICORN_APP=topicpilot_api.main:app

WORKDIR /app

RUN addgroup --system topicpilot \
    && adduser --system --ingroup topicpilot --home /home/topicpilot topicpilot

COPY services/api/ /app/
COPY fixtures/ /fixtures/

RUN if [ -f pyproject.toml ]; then \
      python -m pip install .; \
    elif [ -f requirements.txt ]; then \
      python -m pip install -r requirements.txt; \
    else \
      echo "services/api must provide pyproject.toml or requirements.txt" >&2; exit 1; \
    fi \
    && chown -R topicpilot:topicpilot /app /fixtures

USER topicpilot

EXPOSE 8000

# Keep the image safe when a manually-created Render service does not copy the
# Blueprint start command.  Alembic upgrades are additive/idempotent; no
# importer, fixture seed, reset, or recreate path is part of production start.
CMD ["/bin/sh", "-c", "alembic upgrade head && exec uvicorn ${UVICORN_APP} --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
