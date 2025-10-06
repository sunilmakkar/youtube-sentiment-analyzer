# YouTube Sentiment Analyzer (YSA)

Async FastAPI service that ingests YouTube comments, runs sentiment analysis, and exposes analytics.

## Quickstart
```bash
conda env create -f environment.yml
docker compose up
visit http://localhost:8000/docs
```


---


## `PRD.md`

### 1. Goals and Success Metrics
| Objective                                                                             | Measurable Outcome                                                                                                                    |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Provide org-scoped sentiment analytics for YouTube videos via REST                    | ✔ `/ingest`, `/status`, `/comments`, `/analytics/*` return correct shapes (unit/integration tested) ✔ Idempotent ingestion (no dupes) |
| Demonstrate professional backend craft (FastAPI, Celery, SQLAlchemy, JWT, Docker, CI) | ✔ ≥ 85% coverage (stretch 90%) ✔ GitHub Actions green on every push ✔ `docker compose up` full stack in < 60s on dev                  |
| Operate like production: async jobs, retries, health & observability                  | ✔ `/healthz` reports API/DB/Redis/Celery/model OK ✔ Celery retries/backoff for API quota/5xx ✔ Flower shows active workers            |
| Multi-tenancy & security                                                              | ✔ JWT with `org_id` claim enforced on all data access ✔ Cross-tenant access tests fail with 403                                       |
| Portfolio polish                                                                      | ✔ README with architecture diagram + curl examples ✔ Clear PRD + Roadmap + live Swagger on local/prod                                 |


### 2. Tech Stack Lock-In
- **Language & Runtime:** Python 3.11 (Conda env `ytsa`)
- **API:** FastAPI, Uvicorn (dev), Gunicorn+UvicornWorker (prod), Pydantic v2
- **Auth:** PyJWT / passlib[bcrypt] (JWT access tokens with `org_id`, `role`)
- **Data:** PostgreSQL 16, SQLAlchemy 2.x, Alembic
- **Queue & Cache:** Redis 7, Celery 5, Flower (monitoring)
- **ML (inference only):** HuggingFace Transformers (`distilbert-base-uncased-finetuned-sst-2-english`), torch (CPU), nltk / scikit-learn for keywords/stopwords
- **HTTP & Testing:** httpx, pytest, pytest-asyncio, pytest-cov, Faker
- **Quality:** ruff, black, isort, pre-commit (optional)
- **Containers & CI:** Dockerfile(s), docker-compose (dev/prod), GitHub Actions CI
- **Secrets/Config:** `.env.example` + platform secrets (no real secrets committed)


### 3. Milestones & Check-lists
Work in order; commit & tag at end of each phase (`v0.x`). Keep PRD and README updated.

**Phase 0 — Bootstrap & Environment (½ day)**✅✅✅
- Create repo `youtube-sentiment-analyzer` (MIT/Apache license)☑️
- Add `.gitignore`, `PRD.md` (this), `README.md` placeholder☑️
- Add `requirements.txt`☑️
- Add `.env.example` with: `DATABASE_URL`, `REDIS_URL`, `CELERY_*`, `YOUTUBE_API_KEY`, `SECRET_KEY`, `HF_MODEL_NAME`, `ACCESS_TOKEN_EXPIRE_MINUTES`☑️
- `docker-compose.yml` skeleton: `api`, `worker`, `db`(Postgres), `redis`, `flower`☑️
- Two Dockerfiles in `docker/`: `api.Dockerfile`, `worker.Dockerfile`☑️
- **Exit criteria:** `conda env create -f environment.yml && docker compose up` brings up all services; `GET /docs` loads (empty app OK).☑️

**Phase 1 — App Scaffolding & Health (1 day)**✅✅✅
- FastAPI app factory (`app/main.py`), include routers☑️
- Core config via Pydantic `BaseSettings` (`app/core/config.py`)☑️
- DB engine/session, Base, Alembic init & baseline migration☑️
- Health route `/healthz:` API up, DB ping, Redis ping, Celery ping, HF model “ready=false” (lazy load)☑️
- Structured logging setup☑️
- **Exit criteria:** `alembic upgrade` head runs in container; `/healthz` returns all OK (model can be “not_loaded” but endpoint works).☑️


**Phase 2 — Auth & Multi-Tenancy (1–2 days)**✅✅✅
- Models: `orgs`, `users`, `memberships (role: admin|member)`☑️
- Password hashing (bcrypt), JWT issue/verify; claims include `sub`, `org_id`, `role`, `exp`☑️
- Routes: `/auth/signup`, `/auth/login` (returns access token)☑️
- Dependency that injects `current_user` and `org_id;` protect all non-auth routes☑️
- **Exit criteria:** Auth flow tested; protected route returns 401/403 without/with wrong token; org isolation enforced in queries.☑️


**Phase 3 — Video & Ingestion API (2 days)**✅✅✅
- Tables: `videos(org_id, yt_video_id unique per org, title, channel_id, fetched_at, last_analyzed_at)`☑️
- `POST /ingest?video_id=XYZ`: upsert `videos`, enqueue Celery `fetch_comments(video_id, org_id)`☑️
- `GET /status/{task_id}`: surface Celery task state☑️
- YouTube client service: pagination, normalization, basic backoff on quota (429/403), small request budget per run☑️
- **Exit criteria:** Ingest a real `video_id` → pages fetched and written to DB (idempotent); `/status` shows progress.☑️


**Phase 4 — Comments Persistence & Idempotency (1 day)**✅✅✅
- Tables: `comments(org_id, video_id, yt_comment_id unique per org, author, text, published_at, like_count, parent_id)`☑️
- Deduping service (upsert by `(org_id, yt_comment_id)`); safe re-ingest☑️
- `GET /comments?video_id=...&limit&offset&has_sentiment=bool`☑️
- **Exit criteria:** Re-running ingest does not create duplicates; `/comments` paginates and optionally joins sentiment.☑️


**Phase 5 — Sentiment Inference (2 days)***✅✅✅
- Table: `comment_sentiment(org_id, comment_id unique, label[pos|neg|neu], score, model_name, analyzed_at)`☑️
- HF pipeline lazy-loaded once per worker; batch processing (`BATCH_SIZE` env)☑️
- Celery `analyze_comments(video_id, org_id)`: process only unanalyzed comments☑️
- **Exit criteria:** Batch sentiment persisted; cold worker warms up once; health shows `model.loaded=true` after first inference.☑️


**Phase 6 — Aggregates & Keywords (2 days)**✅✅✅
- Tables: `sentiment_aggregates(org_id, video_id, window_start, window_end, pos_pct, neg_pct, neu_pct, count)`; `keywords(org_id, video_id, term, count, last_updated_at)`☑️
- Celery tasks: `compute_sentiment_trend(video_id, org_id, window='daily')`, `compute_keywords(video_id, org_id, top_k=25)`☑️
- Analytics routes:☑️
 - `GET /analytics/sentiment-trend?video_id=...&window=daily&start&end`☑️
 - `GET /analytics/distribution?video_id=...`☑️
 - `GET /analytics/keywords?video_id=...&top_k=25`☑️
- **Exit criteria:** Trend/distribution/keywords return correct shapes on seeded data.☑️


**Phase 7 — Reliability: Retries, Idempotency, Rate Limits (1 day)**✅✅✅
- Celery autoretry for transient HTTP errors with exponential backoff☑️
- Idempotent task design (safe re-runs); unique DB constraints verified☑️
- Simple per-org rate limit on `/ingest` (in-mem or Redis token bucket)☑️
- **Exit criteria:** Forced transient errors are retried; duplicates prevented; rate-limit responds 429.☑️


**Phase 8 — Testing Pyramid & CI (1–2 days)**✅✅✅
- Unit: youtube client (mock http), sentiment service (mock HF), aggregates, keywords, security☑️
- Integration: `/auth`, `/ingest→DB`, `/analytics/*` shapes; Celery in eager mode or test worker☑️
- Coverage ≥ 85% (stretch 90%); Github Actions: lint → test → build☑️
- **Exit criteria:** Local & CI green; coverage threshold enforced; failing cross-tenant tests prove isolation.☑️


**Phase 9 — API UX & Docs (1 day)**
- Pydantic schemas for request/response; descriptive tags; examples in OpenAPI
- Swagger UI `/docs` + ReDoc `/redoc`
- README sections: problem, quick start (Conda + Docker), curl examples, architecture diagram, limits & future work
- **Exit criteria:** A new dev can run the stack and try cURL in < 10 minutes.


**Phase 10 — Prod Profile & Deploy (1 day, stretch)**
- `docker-compose.prod.yml`: Gunicorn, no reload, resource limits
- Entrypoint to run `alembic upgrade head` on boot
- Platform secrets wired (no `.env` in prod)
- Optional deploy (Fly.io/Render/DO)
- **Exit criteria:** `/healthz OK` in prod stack; logs clean; minimal resources.


---


### 4. Bonus / Future Backlog
| Idea                                             | Value                                 |
| ------------------------------------------------ | ------------------------------------- |
| Celery Beat (scheduled recompute & stale checks) | Autonomously keeps aggregates fresh   |
| Redis caching for hot analytics                  | Low-latency UX under repeated queries |
| WebSocket stream for live ingest sentiment       | Real-time “ticker” during ingestion   |
| Aspect-based sentiment or topic modeling (LDA)   | Deeper insights beyond polarity       |
| Postgres RLS for hard multi-tenancy              | Defense-in-depth at DB layer          |
| OpenTelemetry + Grafana/Tempo/Prom               | Observability story for recruiters    |
| Fly.io/Render deploy with custom domain          | Shareable live demo                   |


---


### 5. Acceptance Checklist (Copy into README)
- Bootstrap: Conda env + Docker stack up; `/docs` & `/healthz` reachable
- Auth: `/auth/signu`p + `/auth/login` issue JWT with `org_id`; protected routes enforce scope
- Ingestion: `/ingest` enqueues; `/status` reflects progress; YouTube pagination stored idempotently
- Persistence: `comments` unique by `(org_id, yt_comment_id)`; re-ingest safe
- Sentiment: batched inference stored in `comment_sentiment`; model loads once per worker
- Analytics: `/analytics/sentiment-trend`, `/distribution`, `/keywords` correct on seeded data
- Reliability: retries/backoff; basic rate-limit on `/ingest`
- Quality: ≥ 85% coverage; CI green; lint/format clean
- Docs: Swagger with examples; README quick-start + curl + diagram
- (Stretch) Prod compose runs with Gunicorn; migrations on boot; `/healthz` OK


---


## `LICENSE` (MIT example)

MIT License

Copyright (c) [2025] [Sunil Makkar]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
