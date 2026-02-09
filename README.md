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
cd api
alembic upgrade head
```

### Seed администратора и базовых настроек

```bash
cd api
python -m app.scripts.seed
```

По умолчанию создаётся админ:
- email: `owner@example.com`
- пароль: `owner123`

## Локальный запуск без Docker

### API

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.scripts.seed
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

Смотрите `.env.example`:
- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_EXPIRES_MINUTES`
- `TELEGRAM_BOT_TOKEN`

### `/web/.env.local` (локальный запуск)

Смотрите `.env.example`:
- `API_INTERNAL_BASE_URL`

### Docker Compose (.env в корне проекта)

Минимум:
- `TELEGRAM_BOT_TOKEN`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

## Админка

URL: http://localhost:3000/admin/login

Возможности:
- управление услугами и категориями
- просмотр записей, смена статуса/прочитано
- настройка расписания, правил записи, контактов, Telegram-уведомлений
