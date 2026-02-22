FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash postgresql-client-common postgresql-client-15 gnupg \
    && bash --version \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN find /app -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; \
    && (chmod +x /app/scripts/*.sh || true)

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
