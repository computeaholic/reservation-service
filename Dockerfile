FROM python:3.12-alpine@sha256:2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk update \
  && apk upgrade \
  && rm -rf /var/cache/apk/*

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --upgrade pip \
  && pip install .[dev] \
  && pip cache purge

COPY . .

RUN adduser -D appuser \
  && chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "reservation_service"]