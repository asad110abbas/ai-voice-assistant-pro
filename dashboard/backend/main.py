import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .database import engine, Base, SessionLocal
from .models import Agent
from .auth import hash_password
from .routers import auth, dashboard, calls, tickets, agents, exports, blocklist, notifications, bot
from .sync import periodic_sync

sync_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sync_task
    Base.metadata.create_all(bind=engine)

    # Add new columns if they don't exist (safe for existing DBs)
    from sqlalchemy import text as _text
    with engine.connect() as _conn:
        for _sql in [
            "ALTER TABLE call_records ADD COLUMN outcome VARCHAR DEFAULT 'bot_handled'",
            "ALTER TABLE call_records ADD COLUMN cost_usd FLOAT DEFAULT 0.0",
        ]:
            try:
                _conn.execute(_text(_sql))
            except Exception:
                pass
        _conn.commit()

    # Create the admin/agent accounts from environment variables if they don't exist yet.
    # Passwords are never hardcoded: set ADMIN_PASSWORD / AGENT_PASSWORD in .env.
    db = SessionLocal()
    try:
        accounts = [
            (os.getenv("ADMIN_EMAIL", "admin@example.com"), "Admin", "admin", os.getenv("ADMIN_PASSWORD")),
            (os.getenv("AGENT_EMAIL", "agent@example.com"), "Agent", "agent", os.getenv("AGENT_PASSWORD")),
        ]
        for email, name, role, password in accounts:
            if not password:
                from loguru import logger
                logger.warning(f"{role.upper()}_PASSWORD not set; skipping seed for {email}")
                continue
            if not db.query(Agent).filter(Agent.email == email).first():
                db.add(Agent(email=email, name=name, role=role, hashed_password=hash_password(password)))
        db.commit()
    finally:
        db.close()

    # Pre-load RAG retriever so first WebSocket connection doesn't time out
    try:
        import sys
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from src.brain.rag import get_retriever
        await asyncio.get_event_loop().run_in_executor(None, get_retriever)
    except Exception as e:
        from loguru import logger
        logger.warning(f"RAG pre-load failed (non-fatal): {e}")

    sync_task = asyncio.create_task(periodic_sync(interval=30))
    yield
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Briha Voice Dashboard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(calls.router)
app.include_router(tickets.router)
app.include_router(agents.router)
app.include_router(exports.router)
app.include_router(blocklist.router)
app.include_router(notifications.router)
app.include_router(bot.router)


@app.get("/")
def root():
    return {"message": "Briha Voice Dashboard API", "version": "1.0.0"}
