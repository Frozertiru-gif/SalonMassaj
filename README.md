# SalonMassaj

Полноценное приложение салона массажа: публичный сайт + API + админка.

## Стек

- `/web` — Next.js (App Router, TS, Tailwind)
- `/api` — FastAPI (async SQLAlchemy, Alembic, JWT)
- Postgres (Docker)

## Быстрый старт (Docker Compose)

```bash
docker compose up -d --build
```

- Web: http://localhost:3000
- API: http://localhost:8000

### Проверка здоровья API

```bash
curl http://localhost:8000/health
```

### Миграции Alembic

```bash
docker compose run --rm migrate
```

Alembic использует синхронный драйвер (psycopg2), поэтому `psycopg2-binary` установлен в `api/requirements.txt`.

### Seed администратора (dev)

```bash
SEED_ADMIN=true ADMIN_EMAIL=owner@example.com ADMIN_PASSWORD=owner123 \
  docker compose run --rm seed
```

Seed не создаёт дубликаты: если админ с таким email уже есть, он не будет пересоздан.

## Локальный запуск без Docker

### API

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
SEED_ADMIN=true ADMIN_EMAIL=owner@example.com ADMIN_PASSWORD=owner123 python -m app.scripts.seed_admin
uvicorn app.main:app --reload
```

### Web

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

## Переменные окружения

### `/api/.env` (локальный запуск)

Смотрите `.env.example`, дополнительно для dev:
- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_EXPIRES_MINUTES`
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `SEED_ADMIN`

### `/web/.env.local` (локальный запуск)

Смотрите `.env.example`:
- `API_INTERNAL_BASE_URL`

### Docker Compose (.env в корне проекта)

Минимум:
- `TELEGRAM_BOT_TOKEN`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SEED_ADMIN` (dev seed администратора)

## Админка

URL: http://localhost:3000/admin/login

Dev-вход:
- email: значение `ADMIN_EMAIL`
- пароль: значение `ADMIN_PASSWORD`

Чтобы сменить пароль, задайте новое значение `ADMIN_PASSWORD`, удалите запись администратора из таблицы `admins`
или обновите её вручную, затем повторно запустите seed-скрипт.

Возможности:
- управление услугами (включая скидки) и категориями
- управление ритуалами недели и отзывами (публикация, сортировка)
- просмотр записей, смена статуса/прочитано
- настройка расписания, правил записи, контактов, Telegram-уведомлений
