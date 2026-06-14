FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY tych/ tych/
COPY main.py .

RUN pip install --no-cache-dir ".[web]"

EXPOSE 8000

CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
