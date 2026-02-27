FROM python:3.12-alpine@sha256:2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache build-base python3-dev postgresql-dev

WORKDIR /build

COPY pyproject.toml ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --upgrade pip \
  && pip wheel --wheel-dir /wheels . \
  && pip cache purge

FROM python:3.12-alpine@sha256:2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache libpq

WORKDIR /app

COPY --from=builder /wheels /wheels

RUN pip install --upgrade pip \
  && pip install --no-index --find-links=/wheels reservation-service \
  && rm -rf /wheels \
  && pip cache purge

COPY alembic ./alembic
COPY alembic.ini ./

RUN adduser -D appuser \
  && chown -R appuser:appuser /app

USER appuser

CMD ["sh", "-c", "python -m reservation_service"]