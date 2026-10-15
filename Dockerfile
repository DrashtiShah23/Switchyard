# Stub image for local compose. Real app install lands with Milestone 3.
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir -e .

CMD ["python", "-c", "print('Switchyard API stub')"]
