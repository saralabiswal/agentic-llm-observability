# Container image for running the observability API in a portable runtime.
# Author: Sarala Biswal

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md* ./
COPY api ./api
COPY audit ./audit
COPY collector ./collector
COPY costs ./costs
COPY drift ./drift
COPY integrations ./integrations
COPY prompts ./prompts
COPY providers ./providers
COPY quality ./quality
COPY seed_data ./seed_data
COPY tracking ./tracking

RUN uv sync --no-dev

EXPOSE 9100

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9100"]
