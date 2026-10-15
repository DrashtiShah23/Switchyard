FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir -e . \
    && mkdir -p /app/data

ENV SWITCHYARD_ENV=local \
    SWITCHYARD_DATABASE_URL=sqlite:///./data/switchyard.db \
    SWITCHYARD_API_KEYS=replace-me:local-developer

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
