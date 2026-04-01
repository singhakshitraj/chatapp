# Chat App Backend (FastAPI + PostgreSQL + Redis + Celery)

Backend service for a real-time chat application with JWT auth, WebSocket messaging, Redis-backed participant caching, and asynchronous background tasks.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.x
- Alembic (schema migrations)
- PostgreSQL
- Redis
- Celery

## What Changed Recently

- Database access is now ORM-based (`SQLAlchemy`) instead of raw SQL queries.
- Schema management now uses `Alembic` migrations instead of manually running `.sql` files.
- Chat/message IDs now use auto-increment integer keys.
- WebSocket participant loading first checks Redis and falls back to PostgreSQL on cache miss.

## Core Features

- JWT-based register/login flow.
- Real-time chat over WebSockets.
- Redis caching for chat participants.
- Offline message tracking through `unread_inbox`.
- Background email task support via Celery + Redis broker.
- Sliding-window request throttling utility (Redis sorted set based).

## Database Models

Defined in `connections/schemas.py`:

- `users`
- `chats`
- `messages`
- `user_chats`
- `unread_inbox`

Create/update schema with Alembic:

```bash
alembic upgrade head
```

## Environment Variables

Create a `.env` file in project root:

```env
# PostgreSQL
HOST=localhost
PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DBNAME=chatapp

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/1

# Email / fastapi-mail
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True

# Throttling
SLIDING_WINDOW_SIZE=60
NUMBER_OF_ALLOWED_REQUESTS=10
```

## Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure PostgreSQL and Redis are running.

3. Run migrations:

```bash
alembic upgrade head
```

4. Start API:

```bash
uvicorn main:app --reload
```

5. Start Celery worker (new terminal):

```bash
celery -A celery_worker.celery_app worker --loglevel=info
```

For Windows, add `--pool=solo` to the Celery command.

## Docker Compose

`docker-compose.yml` defines:

- `web`: FastAPI app (port `8000`)
- `redis`: Redis server (port `6379`)
- `migrate`: one-off Alembic migration runner (`alembic upgrade head`)

Run:

```bash
docker compose up -d
```

If needed, run migrations explicitly:

```bash
docker compose run --rm migrate
```

## API Surface (High Level)

- Auth: `POST /auth/register`, `POST /auth/login`
- Contacts: `GET /contacts/`, `POST /contacts/add`
- Chats: participants + paginated messages under ` /chat/{chat_id}/...`
- WebSocket: `/ws/chat/{chat_id}?token=<jwt>`

## Project Structure

```text
connections/
  connection_db.py
  connection_redis.py
  schemas.py
  ws_connection_manager.py
routers/
  auth.py
  chat.py
  chats_ws.py
  contacts.py
alembic/
  env.py
  versions/
utils/
  exceptions.py
  passwords.py
  send_email.py
  token.py
  validation_models.py
celery_worker.py
main.py
throttling_redis.py
docker-compose.yml
```

