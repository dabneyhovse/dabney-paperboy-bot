FROM python:3.13-slim AS builder

ARG POETRY_VERSION=1.8

ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_CACHE_DIR=/opt/.cache

RUN pip install "poetry==${POETRY_VERSION}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ca-certificates \
    libcups2-dev \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root
