<div align="center">

# 🎙️ AI Voice Assistant

**A bilingual (English / Urdu / Roman Urdu) AI voice agent for e-commerce customer support, with RAG-powered answers, live tool calls, automatic human escalation and a full agent dashboard.**

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?logo=googlegemini&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-FF6F00)
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![BRIHA](https://img.shields.io/badge/Part_of-BRIHA-8B5CF6?labelColor=0B1024)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

> ⚡ **Part of [BRIHA](https://github.com/asad110abbas)**, built by Syed Asad Abbas.

---

## Overview

Customers call or open the voice chat and simply **talk**, in whichever language they're comfortable with.
Briha listens, understands, looks up real data (orders, billing, products, FAQs) and **speaks the answer back**.
When it can't help, or the customer asks for a person, it **hands off to a human agent** with a ticket and the full transcript.

## Architecture

```mermaid
flowchart LR
    C["Customer (browser mic)"] -- "audio over WebSocket" --> WS["FastAPI /ws/voice"]
    WS --> AG["Abuse Guard"]
    AG --> GM["Gemini (audio in, function calling)"]
    GM -- "tool calls" --> T{"Tools"}
    T --> O["get_order_status"]
    T --> B["get_billing_info"]
    T --> P["search_products"]
    T --> F["search_faq (ChromaDB RAG)"]
    O & B & P --> API[("Store REST API")]
    GM --> ESC{"Escalation?"}
    ESC -- "no" --> TTS["Gemini TTS / Edge-TTS fallback"] --> C
    ESC -- "yes" --> TK["Ticket + transcript"] --> D["Agent Dashboard"]
```

## Features

**Voice agent**
- 🗣️ Real-time voice conversation over WebSockets, with speech in and natural speech out
- 🌐 Answers in English, Urdu or Roman Urdu, matching the customer's language automatically
- 🛠️ **Function calling**: order status, billing, product search and FAQ lookup against a REST API
- 📚 **RAG knowledge base**: FAQ documents embedded with Sentence-Transformers and stored in ChromaDB
- 🚨 **Smart escalation**: keyword detection, an unresolved-turn counter and API-failure fallback all create a ticket for a human
- 🛡️ **Abuse guard**: profanity and abuse detection, auto-blocklist, session duration limits
- 💸 Per-session **cost tracking** (audio minutes + output characters)

**Agent dashboard** (React + TypeScript)
- 📊 KPIs and charts: call volume, resolution time, agent performance
- 🎫 Ticket queue with assignment, notes, status workflow and email notifications
- 🎧 Call records with audio playback and full transcripts
- 👥 Agent management (admin / agent roles, JWT auth, bcrypt hashing)
- 📤 Export tickets and calls to PDF / CSV
- 🚫 Blocklist management

## Tech stack

| Layer | Technologies |
|---|---|
| AI | Google Gemini (audio understanding, function calling, TTS), Edge-TTS fallback |
| RAG | ChromaDB, Sentence-Transformers (`all-MiniLM-L6-v2`), python-docx ingestion |
| Backend | Python, FastAPI, WebSockets, SQLAlchemy, PyJWT, passlib/bcrypt, ReportLab, Loguru |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts |
| Testing | pytest (28 tests) with mocked LLM and HTTP layers |
| Ops | Docker, Docker Compose |

## Quick start

```bash
git clone https://github.com/asad110abbas/ai-voice-assistant-pro.git
cd ai-voice-assistant-pro
cp .env.example .env      # add GEMINI_API_KEY, JWT_SECRET, ADMIN_PASSWORD, AGENT_PASSWORD
docker compose up --build
```

- Dashboard: http://localhost:5173 (sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`)
- API docs: http://localhost:8000/docs

**Without Docker:**

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn dashboard.backend.main:app --reload

cd dashboard/frontend && npm install && npm run dev
```

**Tests:**

```bash
pytest -q
```

## Knowledge base

The assistant answers policy questions from `data/sample_faqs.docx`, a **synthetic** FAQ for a fictional electronics store.
To use your own, write one paragraph per answer in the form `"Topic: <name>. <answer>"` and point `FAQ_PATH` at the file.
Regenerate the sample with `python scripts/make_sample_faqs.py`.

The store API (`STORE_API_URL`) is optional. Without it, the assistant still talks, answers FAQs and escalates.

## Project structure

```
src/
  api/store_client.py     REST client for orders, billing, products, tickets
  brain/                  RAG retriever, escalation logic, conversation memory
  multimodal/             Gemini client: audio -> tools -> response
  abuse_guard.py          abuse detection and blocklist
dashboard/
  backend/                FastAPI app, routers, auth, exports, email
  frontend/               React + TypeScript dashboard
config/settings.py        environment-driven configuration
tests/                    pytest suite
```

## Deployment

| Target | How |
|---|---|
| ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) **Docker Compose** | `docker compose up --build` runs the FastAPI voice backend and the React dashboard as containers |

## License

[MIT](LICENSE)
