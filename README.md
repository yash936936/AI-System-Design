# SysDesign AI 

An AI-powered system design tool built to generate professional-grade, structured reference architectures. SysDesign AI detects whether you need High-Level Design (HLD) or Low-Level Design (LLD), asks clarifying questions via interactive MCQs, and pulls from real-world reference architectures (via RAG) to generate complete system designs—all within a familiar, frictionless chat interface.

---

## 🚀 Key Features

* **Intelligent Intent Detection:** Automatically classifies user prompts as HLD or LLD before proceeding.
* **Structured Clarification (MCQ):** Gathers non-functional requirements, functional requirements, and constraints before generating architecture.
* **RAG-Powered Generation:** Ingests system design GitHub repos and canonical architectures (e.g., Netflix, X/Twitter, Uber) to ground AI responses in real-world engineering practices.
* **Claude-Style Interactive UI:** A three-panel layout featuring chat history, a main chat area, and an artifact panel for progressive rendering.
* **Comprehensive Artifact Output:** Generates interactive architecture diagrams (React Flow/Mermaid), capacity estimates, data models, API schemas, and tech stack recommendations.
* **Export & Sharing:** Download completed design packages as PDF or Markdown, or share them via public links.

---

## 🏗 Tech Stack & Architecture

SysDesign AI operates as a monorepo utilizing a modern Python/Node stack.

### Frontend
* **Framework:** Next.js 14 (App Router)
* **State Management:** Zustand (Session, MCQ, and Artifact tab state)
* **UI & Styling:** Tailwind CSS 
* **Diagram Rendering:** React Flow (interactive components) + Mermaid (fallback).

### Backend
* **Framework:** FastAPI (Python 3.11) with async support for Server-Sent Events (SSE) streaming.
* **AI & LLM:** Google Gemini (`gemini-2.5-flash` for generation, `gemini-embedding-001` for embeddings) via `google-generativeai`.
* **RAG Pipeline:** LangChain, ChromaDB (local persistence, upgrading to pgvector), and PyGithub for repo ingestion.
* **Database & ORM:** PostgreSQL (via Supabase) with async SQLAlchemy and Alembic migrations.
* **Caching & Limits:** Upstash Redis (response caching & rate limiting).
* **Storage:** Cloudflare R2 for staging payloads and exporting PDFs (via WeasyPrint/html2canvas).

---

## 📂 Monorepo Structure

```text
sysdesign-v2/
├── backend/                  ← FastAPI (Python 3.11)
│   ├── app/
│   │   ├── api/routes/       ← Route handlers (classify, mcq, generation, etc.)
│   │   ├── core/             ← Config, Gemini client, rate limiter
│   │   ├── db/               ← SQLAlchemy models & sessions
│   │   ├── schemas/          ← Pydantic request/response schemas
│   │   └── services/         ← Business logic (RAG pipeline, MCQ generation)
│   ├── alembic/              ← DB migrations
│   ├── prompts/              ← Versioned prompt text files
│   ├── scripts/              ← GitHub & Canonical designs ingestion scripts
│   ├── main.py               ← FastAPI app entry point
│   └── requirements.txt      ← Python dependencies
│
├── frontend/                 ← Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/              ← Route definitions & API wrappers
│   │   ├── components/       ← UI (chat, artifact panel, interactive diagrams)
│   │   ├── lib/              ← API client, SSE hook, utils
│   │   ├── hooks/            ← Custom React hooks
│   │   ├── store/            ← Zustand state stores
│   │   └── types/            ← Shared TypeScript types
│   └── package.json          ← Node dependencies
│
└── docs/                     ← System design documentation

```

---

## 🗄️ Database Schema Summary

The primary database is **PostgreSQL**, managed with Alembic. Key tables include:

* `users`: Account and plan mapping (free vs pro).
* `sessions`: Stores the full MCQ context object and tracks generation status.
* `rag_retrievals`: Logs retrieval results and confidence scores for cache warm-up and evaluation.
* `generation_outputs`: Holds payloads for architecture, capacity, data model, API, and tech stack.
* `famous_designs`: Pre-loaded canonical system designs (e.g., Netflix CDN, WhatsApp).
* `gemini_usage`: Daily API call rollups for proactive free-tier limit management.

---

## 🔌 Core API Endpoints

The API is mounted at `https://api.sysdesign.ai/v1`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/classify` | Classifies prompt intent as LLD or HLD. |
| `GET` | `/api/mcq/:design_type` | Retrieves the dynamic MCQ template. |
| `POST` | `/api/sessions` | Creates a new design session with the MCQ context object. |
| `GET` | `/api/sessions/:id/retrieve` | Triggers RAG retrieval against GitHub chunks and famous designs. |
| `GET` | `/api/sessions/:id/stream` | Opens an SSE connection streaming generation events. |
| `POST` | `/api/sessions/:id/chat` | Handles context-aware follow-up questions. |
| `POST` | `/api/sessions/:id/export` | Generates a signed R2 URL for downloading a PDF/Markdown bundle. |

---

## 🛠 Quick Start

### Prerequisites

* Python 3.11+
* Node.js 18+
* PostgreSQL instance (e.g., local or Supabase)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env            
# Add your GEMINI_API_KEY and DATABASE_URL to .env

# Apply Database Schema
alembic upgrade head            

# Run the Dev Server
uvicorn main:app --reload --port 8000

```

### Frontend Setup

```bash
cd frontend
npm install

# Configure Environment Variables
cp .env.local.example .env.local   
# Ensure NEXT_PUBLIC_API_URL is pointed to http://localhost:8000

# Run the Dev Server
npm run dev                         
# Open http://localhost:3000

```

---
