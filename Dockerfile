FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install -e ".[dev]"

COPY . .

RUN chmod +x ./ves

CMD ["python3", "-m", "pytest", "tests/", "-v"]
