# Database Schema — SysDesign AI (v2)

> Engine: PostgreSQL 15 via Supabase
> ORM: SQLAlchemy (async) with Alembic migrations
> All PKs: UUID via `gen_random_uuid()`
> All timestamps: TIMESTAMPTZ in UTC

---

## Table: `users`

```sql
CREATE TABLE users (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email      TEXT NOT NULL UNIQUE,
  name       TEXT,
  avatar_url TEXT,
  plan       TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_users_email ON users(email);
```

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `email` | TEXT | From Google OAuth |
| `plan` | TEXT | `free` (5 sessions/day) or `pro` (50/day) |

---

## Table: `sessions`

One row per design session. The `context_json` column stores the full MCQ output object — this is the single source of truth fed into every LLM call.

```sql
CREATE TABLE sessions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
  prompt        TEXT NOT NULL,
  design_type   TEXT CHECK (design_type IN ('HLD', 'LLD')),
  system_name   TEXT,
  context_json  JSONB NOT NULL DEFAULT '{}',
  status        TEXT NOT NULL DEFAULT 'clarifying'
                CHECK (status IN ('clarifying', 'retrieving', 'generating', 'complete', 'failed')),
  is_public     BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at  TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status  ON sessions(status);
CREATE INDEX idx_sessions_created ON sessions(created_at DESC);
```

| Column | Notes |
|---|---|
| `design_type` | Set after Phase A classification |
| `system_name` | Extracted from prompt if identifiable (e.g. "Twitter") |
| `context_json` | Full MCQ answers object — see workflow.md for schema |
| `status` | Progresses: clarifying → retrieving → generating → complete |

---

## Table: `rag_retrievals`

Stores every retrieval result. Used for: eval of RAG quality, cache warm-up, debugging low-quality generations.

```sql
CREATE TABLE rag_retrievals (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id         UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  query              TEXT NOT NULL,
  chunks_json        JSONB NOT NULL DEFAULT '[]',
  max_score          NUMERIC(4,3),
  used_web_fallback  BOOLEAN NOT NULL DEFAULT FALSE,
  famous_match       TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_session ON rag_retrievals(session_id);
```

| Column | Notes |
|---|---|
| `chunks_json` | Array of `{id, source, section, text, score}` objects |
| `max_score` | Highest cosine similarity score — used to evaluate RAG quality over time |
| `famous_match` | Name of the famous design matched (e.g. `"twitter"`) or null |

---

## Table: `generation_outputs`

One row per output section per session. Payload JSON stored in R2 — only the URL here.

```sql
CREATE TABLE generation_outputs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  section      TEXT NOT NULL
               CHECK (section IN ('architecture', 'capacity', 'data_model', 'api_design', 'stack')),
  status       TEXT NOT NULL DEFAULT 'pending'
               CHECK (status IN ('pending', 'generating', 'complete', 'error')),
  payload_url  TEXT,
  tokens_used  INTEGER DEFAULT 0,
  cached       BOOLEAN NOT NULL DEFAULT FALSE,
  duration_ms  INTEGER DEFAULT 0,
  error_msg    TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, section)
);

CREATE INDEX idx_gen_outputs_session ON generation_outputs(session_id);
```

| Column | Notes |
|---|---|
| `cached` | TRUE if this was served from Redis response cache — no Gemini call made |
| `payload_url` | Pre-signed R2 URL to section JSON payload |

---

## Table: `gemini_usage`

Daily rollup of all Gemini API calls. Critical for monitoring free-tier consumption and triggering alerts before hitting RPD limits.

```sql
CREATE TABLE gemini_usage (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date           DATE NOT NULL,
  model          TEXT NOT NULL,
  total_calls    INTEGER NOT NULL DEFAULT 0,
  tokens_in      INTEGER NOT NULL DEFAULT 0,
  tokens_out     INTEGER NOT NULL DEFAULT 0,
  cached_calls   INTEGER NOT NULL DEFAULT 0,
  UNIQUE (date, model)
);

CREATE UNIQUE INDEX idx_gemini_usage_date_model ON gemini_usage(date, model);
```

> This table is updated by an UPSERT after every Gemini call. A cron job checks this at 80% of RPD limit and sends a Slack alert.

---

## Table: `famous_designs`

Pre-loaded canonical designs. Populated by a one-time ingestion script, updated manually on major architecture changes.

```sql
CREATE TABLE famous_designs (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  system_name    TEXT NOT NULL UNIQUE,
  title          TEXT NOT NULL,
  canonical_json JSONB NOT NULL DEFAULT '{}',
  diagram_json   JSONB NOT NULL DEFAULT '{}',
  key_insights   TEXT[] NOT NULL DEFAULT '{}',
  sources        TEXT[] NOT NULL DEFAULT '{}',
  last_updated   DATE NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_famous_designs_name ON famous_designs(system_name);
```

**Pre-loaded systems at launch:** netflix, twitter, whatsapp, meta, uber, youtube, airbnb

`canonical_json` structure:
```json
{
  "capacity": {},
  "data_model": {},
  "api_design": {},
  "stack": {}
}
```

---

## Table: `exports`

```sql
CREATE TABLE exports (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id    UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
  format        TEXT NOT NULL CHECK (format IN ('pdf', 'markdown', 'json')),
  sections      TEXT[] NOT NULL,
  download_url  TEXT NOT NULL,
  storage_key   TEXT NOT NULL,
  size_bytes    INTEGER,
  expires_at    TIMESTAMPTZ NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exports_session ON exports(session_id);
CREATE INDEX idx_exports_expires ON exports(expires_at);
```

---

## Entity Relationship Summary

```
users
  └── sessions (user_id → users.id, nullable)
        ├── rag_retrievals     (session_id, cascade delete)
        ├── generation_outputs (session_id, cascade delete)
        └── exports            (session_id, cascade delete)

gemini_usage  (standalone — no FK, daily rollup)
famous_designs (standalone — populated by ingestion script)
```

---

## Migration Strategy

- Managed with **Alembic** (`alembic revision --autogenerate`)
- Migration files: `backend/alembic/versions/`
- Never edit a migration after applying to production
- Run `alembic upgrade head` in CI before every deploy

```bash
# Generate new migration
alembic revision --autogenerate -m "add gemini_usage table"

# Apply
alembic upgrade head

# Rollback one step
alembic downgrade -1
```