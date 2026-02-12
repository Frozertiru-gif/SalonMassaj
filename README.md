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
Создаваемый через seed пользователь получает роль `SYS_ADMIN`.

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
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_BOT_USERNAME`
- `TELEGRAM_ADMIN_IDS`
- `TELEGRAM_SYS_ADMIN_IDS`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `SEED_ADMIN`

### `/web/.env.local` (локальный запуск)

Смотрите `.env.example`:
- `API_INTERNAL_BASE_URL`

### Docker Compose (.env в корне проекта)

Минимум:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_BOT_USERNAME`
- `TELEGRAM_ADMIN_IDS`
- `TELEGRAM_SYS_ADMIN_IDS`
- `TELEGRAM_MODE` (`polling` для локального Docker, `webhook` для публичного HTTPS URL)
- `LOG_LEVEL` (`INFO` для подробных логов Telegram)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SEED_ADMIN` (dev seed администратора)

## Админка

URL: http://localhost:3000/admin/login

Dev-вход:
- email: значение `ADMIN_EMAIL`
- пароль: значение `ADMIN_PASSWORD`

Чтобы сменить пароль, задайте новое значение `ADMIN_PASSWORD`, удалите запись администратора из таблицы `admins`
или обновите её вручную, затем повторно запустите seed-скрипт.

Роли:
- `ADMIN` — стандартная админка.
- `SYS_ADMIN` — все права `ADMIN` + вкладка `Логи` (`/admin/logs`) и доступ к `GET /admin/logs`.

Возможности:
- управление услугами (включая скидки) и категориями
- управление ритуалами недели и отзывами (публикация, сортировка)
- просмотр записей, смена статуса/прочитано
- настройка расписания, правил записи, контактов, Telegram-уведомлений
- просмотр аудит-лога действий (только `SYS_ADMIN`)


## Привязка Telegram для мастера

1. Откройте админку: `http://localhost:3000/admin/masters`.
2. В карточке мастера нажмите **«Сгенерировать ссылку»** — появится **код привязки**.
3. Мастер должен открыть вашего Telegram-бота и отправить команду:
   - `/start <код_привязки>`
4. После этого у мастера в админке поле `TG` станет **«привязан»**, а `Chat ID` заполнится автоматически.

Если бот в ответ пишет «Код привязки не найден или устарел», сгенерируйте новый код и отправьте повторно.

## Telegram-доступ админов

Доступ к админским действиям Telegram-бота определяется **только по Telegram `user_id`** (whitelist),
без логина/пароля в чате.

Источник allowlist:
1. ENV (приоритетно):
   - `TELEGRAM_ADMIN_IDS` — список через запятую, например `123,456`
   - `TELEGRAM_SYS_ADMIN_IDS` — список через запятую, например `789,999`
2. Если ENV не задан, используются настройки в БД:
   - `tg_admin_ids`
   - `tg_sys_admin_ids`

Поддерживаемые команды:
- `/admin` — для `ADMIN` и `SYS_ADMIN`
- `/sys` — только для `SYS_ADMIN`

`SYS_ADMIN` наследует все админские Telegram-права.

## Аудит-лог

Сервер пишет события в таблицу `audit_logs` (не в браузер).
Для просмотра используется endpoint `GET /admin/logs` (только `SYS_ADMIN`) и страница админки `/admin/logs`.


## Telegram: почему «бот молчит» и в логах пусто

Чаще всего причина в режиме `webhook` без публичного HTTPS webhook URL.
В Docker Compose по умолчанию используется `TELEGRAM_MODE=polling`, поэтому бот сам забирает апдейты через `getUpdates` и должен работать локально без проброса webhook.

Быстрая диагностика:

```bash
curl -s http://localhost:8000/admin/telegram/webhook-info
```

Проверьте:
- `diagnostics.telegram_mode` — ожидаемо `polling` для локальной разработки
- `diagnostics.token_configured` — должен быть `true`
- если выбран `webhook`, должен быть валидный `current_webhook_url`

