FROM python:3.12.8-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml /app/pyproject.toml

RUN python -m pip install --no-cache-dir --upgrade pip==24.3.1 && \
    python -m pip install --no-cache-dir \
      black==24.10.0 \
      ruff==0.8.4 \
      mypy==1.13.0 \
      pytest==8.3.4 \
      pytest-cov==6.0.0 \
      pre-commit==4.0.1

CMD ["bash"]