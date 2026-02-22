# Pin to Debian bookworm: it provides postgresql-client-15 in the default repos.
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash gnupg postgresql-client-common postgresql-client-15 \
    && bash --version \
    && gpg --version | head -n 1 \
    && psql --version | grep -E ' 15(\.| )' \
    && pg_dump --version | grep -E ' 15(\.| )' \
    && pg_restore --version | grep -E ' 15(\.| )' \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN find /app -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; \
    && (chmod +x /app/scripts/*.sh || true)

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
