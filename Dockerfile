FROM python:3.12-slim

RUN apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .

RUN pip install -e ".[dev]"

COPY . .

COPY .vesconfig /root/.vesconfig

RUN chmod +x ./ves

CMD ["python3", "-m", "pytest", "tests/", "-v"]
