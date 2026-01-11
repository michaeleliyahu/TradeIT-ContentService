# Content Service

Short description: FastAPI service for likes, comments, and engagement counters, consuming post events and publishing engagement events.

## 🎯 Responsibilities
- Manage likes and comments for posts
- Maintain per-post counters (likes_count, comments_count)
- Consume post lifecycle events from RabbitMQ
- Publish engagement events (liked, unliked, commented, comment deleted)

Out of scope:
- ❌ User authentication/issuance (relies on Identity Service)
- ❌ Post CRUD (handled by Post Service)
- ❌ Feed generation

## 🏗️ Architecture
- Framework: FastAPI (async)
- Architecture: Layered (routers → services → repositories → DB/models)
- Likely layers: api/routers, services, repositories, models (SQLAlchemy), schemas (Pydantic), messaging (RabbitMQ via aio-pika)

Folder sketch (indicative):
```
app/
 ├─ api/
 ├─ services/
 ├─ repositories/
 ├─ models/
 ├─ schemas/
 ├─ messaging/
 └─ main.py
```

## 🔌 External Dependencies
- PostgreSQL
- RabbitMQ
- Identity Service (JWT validation for write actions)

## 🔄 Service Communication
### 📥 Events – Consumer
- Exchange: `post_events`
- Routing keys: `post.created`, `post.deleted`

### 📤 Events – Publisher
- Exchange: `content_events`
- Routing keys:
	- `content.post.liked`
	- `content.post.unliked`
	- `content.post.commented`
	- `content.comment.deleted`

## 🌐 REST APIs (Overview)
- `POST   /posts/{post_id}/like`
- `DELETE /posts/{post_id}/like`
- `POST   /posts/{post_id}/comments`
- `GET    /posts/{post_id}/comments`
- `DELETE /comments/{comment_id}`
- `GET    /posts/{post_id}/stats`
- `GET    /health`, `GET /health/detailed`

## ⚙️ Environment (.env)
- `DATABASE_URL` (e.g., postgresql://user:pass@host:5432/content_db)
- `RABBITMQ_URL` (e.g., amqp://guest:guest@rabbitmq:5672/)
- `POST_EXCHANGE` (default `post_events`)
- `POST_QUEUE` (default `content_post_events`)
- `POST_CREATED_ROUTING_KEY` (default `post.created`)
- `POST_DELETED_ROUTING_KEY` (default `post.deleted`)
- `CONTENT_EXCHANGE` (default `content_events`)
- `CONTENT_ROUTING_PREFIX` (default `content`)
- `JWT_SECRET_KEY`, `JWT_ALGORITHM` (default `HS256`)
- `DEFAULT_PAGE_SIZE` (default `20`), `MAX_PAGE_SIZE` (default `100`)
- `SERVICE_NAME`, `SERVICE_VERSION`, `DEBUG`
- No `.env.example` noted; create manually if missing

## ▶️ Local Run
```bash
python -m venv venv
source venv/bin/activate  # or Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
python run.py
```

## Docker
```bash
docker-compose up --build
```

## 🧪 Tests
- Add a pytest suite under `tests/` (not included yet)

## 🧠 Notes / Design Decisions
- Event-driven: consumes post lifecycle events to keep engagement data consistent
- Database per service for ownership and isolation
- Engagement events allow other services to react without tight coupling

## 🔐 Authentication Model
- JWTs issued by the Identity Service
- Algorithm: HS256 (default across services)
- Claims: `sub` = user_id, plus `exp`, `iat`
- Tokens are validated locally (no runtime call to Identity Service); ensure the signing key matches the Identity Service configuration
