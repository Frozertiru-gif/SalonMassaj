# SalonMassaj

Полноценное приложение салона массажа: публичный сайт + API + админка.

## Стек

- `/web` — Next.js (App Router, TS, Tailwind)
- `/api` — FastAPI (async SQLAlchemy, Alembic, JWT)
- Postgres (Docker)

## Быстрый старт (Docker Compose)

```bash
cp .env.example .env
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

### Пересоздание БД и проверка миграций

```bash
docker compose down -v
docker compose up -d db
docker compose run --rm migrate
```

Проверки после успешного `alembic upgrade head`:

```bash
docker compose exec db psql -U postgres -d salon -c "SELECT version_num, pg_catalog.format_type(a.atttypid, a.atttypmod) AS version_type FROM alembic_version v JOIN pg_catalog.pg_attribute a ON a.attrelid = 'alembic_version'::regclass AND a.attname = 'version_num' LIMIT 1;"
docker compose exec db psql -U postgres -d salon -c "\d masters"
```

Ожидаемо:
- `alembic_version.version_num` имеет тип `character varying(255)` (или больше).
- В `masters` есть колонка `telegram_chat_id` и индекс `ix_masters_telegram_chat_id`.

### Seed админ-аккаунтов (dev)

```bash
SEED_ADMIN=true \
SYS_ADMIN_EMAIL=owner@example.com SYS_ADMIN_PASSWORD=owner123 \
ADMIN_EMAIL=manager@example.com ADMIN_PASSWORD=manager123 \
  docker compose run --rm seed
```

Seed поддерживает два аккаунта:
- `SYS_ADMIN_*` — системный администратор.
- `ADMIN_*` — обычный администратор (опционально).

Seed работает как upsert: если email уже существует, роль/пароль/active обновляются по ENV.

## Локальный запуск без Docker

### API

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
SEED_ADMIN=true SYS_ADMIN_EMAIL=owner@example.com SYS_ADMIN_PASSWORD=owner123 ADMIN_EMAIL=manager@example.com ADMIN_PASSWORD=manager123 python -m app.scripts.seed_admin
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

### Docker Compose (`/.env`)

- `api`, `migrate`, `seed` читают переменные из `/.env`.
- Для Docker `DATABASE_URL` должен указывать на сервис Postgres `db`:
  - `postgresql+asyncpg://postgres:postgres@db:5432/salon`
- Быстрый старт: `cp .env.example .env`.

### Локальный запуск API вне Docker (`/api/.env`)

- Шаблон: `/api/.env.example`.
- Файл `api/.env.example` намеренно минимальный: в нём только значения,
  которые обычно отличаются от корневого `/.env`.
- Остальные переменные можно копировать из `/.env.example` по мере необходимости.
- `SYS_ADMIN_EMAIL`/`SYS_ADMIN_PASSWORD` (и опционально `ADMIN_EMAIL`/`ADMIN_PASSWORD`) обычно задаются инлайн только для seed-команды.
- Для локального запуска `DATABASE_URL` должен указывать на `localhost`:
  - `postgresql+asyncpg://postgres:postgres@localhost:5432/salon`

### `/web/.env.local` (локальный запуск web)

Смотрите `web/.env.example`:
- `API_INTERNAL_BASE_URL`

### Backup env (`/api/scripts/backup.env`)

- Шаблон: `/api/scripts/backup.env.example`.
- `DATABASE_URL` в backup env должен совпадать с Docker-конфигом и использовать `@db:5432`.

## Админка

URL: http://localhost:3000/admin/login

Dev-вход (если seed запущен с двумя аккаунтами):
- `SYS_ADMIN`: `SYS_ADMIN_EMAIL` / `SYS_ADMIN_PASSWORD`
- `ADMIN`: `ADMIN_EMAIL` / `ADMIN_PASSWORD`

Если меняете пароль/роль — просто перезапустите seed с новыми ENV,
скрипт обновит существующие записи в `admins`.

Роли:
- `ADMIN` — стандартная админка.
- `SYS_ADMIN` — все права `ADMIN` + вкладка `Логи` (`/admin/logs`) и доступ к `GET /admin/logs`.

Роль для токена админки задаётся только через ENV:
- `SYS_ADMIN_TOKENS=` — пустой список токенов
- `SYS_ADMIN_TOKENS=token1,token2` — CSV
- `SYS_ADMIN_TOKENS=["token1","token2"]` — JSON-массив
- `ADMIN_TOKENS=token3,token4`

Если один и тот же токен случайно указан в обоих списках, API пишет warning и считает его `SYS_ADMIN`.

### Как зайти с двумя ролями (`ADMIN` и `SYS_ADMIN`)

1. Поднимите проект и убедитесь, что API/WEB запущены.
2. Один раз выполните seed с двумя парами логинов:

   ```bash
   SEED_ADMIN=true \
   SYS_ADMIN_EMAIL=owner@example.com SYS_ADMIN_PASSWORD=owner123 \
   ADMIN_EMAIL=manager@example.com ADMIN_PASSWORD=manager123 \
     docker compose run --rm seed
   ```

3. Вход как `SYS_ADMIN`: `owner@example.com` / `owner123`.
4. Вход как `ADMIN`: `manager@example.com` / `manager123`.
5. Проверка роли:
   - у `SYS_ADMIN` есть вкладка **«Логи»** (`/admin/logs`),
   - у `ADMIN` этой вкладки нет.

Важно:
- если `SYS_ADMIN_*` не заданы, для обратной совместимости `ADMIN_*` создадут именно `SYS_ADMIN`.
- если `ADMIN_EMAIL` совпадает с `SYS_ADMIN_EMAIL`, будет создан только один пользователь с ролью `SYS_ADMIN`.

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


## Backups (PostgreSQL)

В API добавлен автоматический encrypted backup:
- ежедневный запуск в `03:15 UTC` (`BACKUP_CRON_HOUR` / `BACKUP_CRON_MINUTE`),
- catch-up при старте, если последняя копия старше 24 часов,
- файлы в `BACKUP_DIR` (`*.dump.gpg`) + `last_backup.json`,
- retention через `RETENTION_KEEP`.
- backup-скрипт исполняется через `bash`, поэтому `bash` должен быть установлен внутри API-контейнера (в текущем `api/Dockerfile` уже установлен).

Обязательные ENV:
- `BACKUP_ENABLED=true`
- `BACKUP_CHAT_ID=<telegram_chat_id>`
- `BACKUP_PASSPHRASE=<пароль шифрования>`

В Docker Compose уже подключены:
- `./api/backups:/app/backups`
- `./api/scripts:/app/scripts`

Управление доступно в Telegram только для `SYS_ADMIN` в личном чате через кнопку **«🛡 Резервные копии»**.
Восстановление требует явного подтверждения inline-кнопкой.
