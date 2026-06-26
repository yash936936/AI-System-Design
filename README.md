# SysDesign AI — Stage 1: Scaffold & Infrastructure

## Monorepo Structure

```
sysdesign-v2/
├── backend/                  ← FastAPI (Python 3.11)
│   ├── app/
│   │   ├── api/routes/       ← Route handlers
│   │   ├── core/             ← Config, Gemini client, rate limiter
│   │   ├── db/               ← SQLAlchemy models, migrations
│   │   ├── schemas/          ← Pydantic request/response schemas
│   │   └── services/         ← Business logic (classify, mcq, pipeline)
│   ├── alembic/              ← DB migrations
│   ├── prompts/              ← Versioned prompt text files
│   ├── scripts/              ← Ingestion scripts
│   ├── main.py               ← FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                 ← Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/              ← Routes
│   │   ├── components/       ← UI, layout, chat, artifact, mcq
│   │   ├── lib/              ← API client, SSE hook, utils
│   │   ├── hooks/            ← Custom React hooks
│   │   ├── store/            ← Zustand stores
│   │   └── types/            ← Shared TypeScript types
│   ├── package.json
│   └── .env.local.example
│
└── docs/                     ← Symlink to ../redesign-docs
```

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Fill in GEMINI_API_KEY + DATABASE_URL
alembic upgrade head            # Apply DB schema
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # Fill in NEXT_PUBLIC_API_URL
npm run dev                         # http://localhost:3000
```

## Stage 1 Deliverables Checklist

- [x] Monorepo directory structure
- [x] FastAPI app with CORS, health check
- [x] PostgreSQL schema (7 tables) via SQLAlchemy + Alembic
- [x] Gemini API client with rate limiter (14 RPM semaphore)
- [x] `/api/classify` endpoint (Phase A)
- [x] `/api/mcq/:design_type` endpoint (Phase B — static templates)
- [x] `/api/sessions` POST — session creation
- [x] Pydantic schemas for all request/response types
- [x] Next.js 14 app with three-panel Claude.ai layout
- [x] Zustand session store
- [x] Tailwind config with Claude.ai colour tokens
- [x] API client with TypeScript types
- [x] `.env.example` files for both services
