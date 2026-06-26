# PRD — SysDesign AI (v2)

## Problem Statement

System design is one of the hardest skills to learn and one of the most time-consuming artifacts to produce. Students preparing for interviews get generic answers from ChatGPT that skip the reasoning. Engineers designing real systems spend days doing research they've already done before. There is no tool that (1) understands whether you need a high-level or low-level design, (2) asks the right clarifying questions before generating anything, (3) pulls from real-world reference architectures, and (4) produces output in a structured, shareable format — all within a familiar, frictionless chat interface.

---

## User Personas

### IN — Interview Candidate
*CS student or engineer preparing for FAANG/startup system design rounds*
Needs to practise HLD for specific systems (design Twitter, design WhatsApp). Wants to see canonical architectures explained with trade-off reasoning, not just a diagram dump.

### DE — Developer / Founder
*Solo or small team building a real product*
Needs LLD for a specific component they're building. Wants capacity estimates, data model, API design, and a concrete tech stack — not a generic "use PostgreSQL" recommendation.

### SA — Solutions Architect
*Agency or enterprise pre-sales*
Needs professional-grade design docs fast. Values export quality and the ability to show famous reference designs to clients ("this is how Netflix does it, here's how yours would differ").

### ED — Educator / Team Lead
*Teaching system design internally or in bootcamps*
Wants to generate reference designs for well-known systems to use as teaching material. Needs designs to be accurate, sourced, and reproducible.

---

## Core Feature Requirements — MoSCoW

| Feature | Priority | Description |
|---|---|---|
| LLD / HLD auto-detection | **Must** | Classify user intent as Low-Level or High-Level Design before proceeding |
| Structured MCQ clarification | **Must** | Ask targeted questions (functional reqs, NFRs, capacity, data model, API, arch, bottlenecks, scalability, trade-offs) via interactive MCQ + free-text fields |
| RAG from GitHub repos | **Must** | Ingest system design repos from GitHub; retrieve relevant chunks before generating |
| Pre-loaded famous designs | **Must** | Netflix, X (Twitter), WhatsApp, Meta, Uber, YouTube, Airbnb stored and retrievable by name or similarity |
| Claude.ai-identical UI | **Must** | Sidebar (chat history), main chat area, artifact panel — pixel behaviour match |
| Gemini API (free tier) | **Must** | All LLM calls use Gemini; no paid tier; strict RPD/TPM/RPM controls |
| Architecture diagram output | **Must** | Interactive component graph in artifact panel |
| Tech stack recommendation | **Must** | Layer-by-layer with rationale tied to clarification answers |
| Capacity estimation section | **Must** | Back-of-envelope QPS, storage, bandwidth from NFR answers |
| Data model output | **Must** | Entity schema, SQL/NoSQL decision, access patterns |
| API design section | **Must** | Key endpoints, request/response shapes, auth strategy |
| Web search fallback | **Should** | If RAG returns low-confidence results, search the web before generating |
| PDF / Markdown export | **Should** | Full design package as downloadable file |
| Famous design retrieval | **Should** | "Show me how Netflix does CDN" → pulls stored canonical design |
| Conversation history (sidebar) | **Should** | Past sessions listed in sidebar, resumable |
| Shareable read-only link | **Could** | Generate a public URL for a completed design |
| Version diff | **Could** | Compare two runs of the same system |
| GitHub repo scaffold | **Won't (v1)** | Generate boilerplate from the design |

---

## Success Metrics

| Metric | Target |
|---|---|
| LLD/HLD classification accuracy | > 95% |
| MCQ completion rate (users who finish all questions) | > 70% |
| RAG hit rate (relevant chunk retrieved) | > 80% |
| Time from MCQ complete to first output token | < 10s |
| Gemini API RPD usage vs free tier limit | < 70% of daily cap |
| Famous design retrieval accuracy (user rates as correct) | > 90% |
| Export rate per completed session | > 50% |
| Week-2 retention | > 35% |

---

## Phased Roadmap (6 Development Stages)

### Stage 1 — Scaffold & Infrastructure · Week 1–2
Project monorepo, Next.js frontend shell, FastAPI backend shell, PostgreSQL schema applied, Gemini API client wired, local dev environment documented.

### Stage 2 — LLD/HLD Classifier + MCQ Clarification · Week 3–4
Intent classifier (LLD vs HLD). Dynamic MCQ question set from 9 categories. Interactive MCQ UI in chat panel (option chips + free-text override). Context object built from answers.

### Stage 3 — RAG Pipeline · Week 5–7
GitHub repo ingestion (target repos defined). Chunking, embedding (Gemini `text-embedding-004`), vector store (ChromaDB or pgvector). Famous designs pre-loaded. Retrieval + reranking before generation. Web search fallback.

### Stage 4 — Generation Pipeline · Week 8–10
Architecture diagram generation from context + RAG chunks. Capacity estimation. Data model. API design. Tech stack. All streamed to artifact panel.

### Stage 5 — Claude.ai UI · Week 11–12
Sidebar with history. Chat panel with message bubbles. Artifact panel with tabs (Diagram / Capacity / Data Model / API / Stack). MCQ rendered as interactive chips inside chat. Full streaming display.

### Stage 6 — Export, Sharing & Cost Optimisation · Week 13–14
PDF/MD export. Shareable links. Gemini cost controls: response caching, prompt compression, RPM throttle middleware, batch embedding. Load testing and cost audit.