import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from .models import CallRecord, EscalationTicket, Agent, Notification
from .database import SessionLocal

SESSIONS_DIR = os.getenv("SESSIONS_DIR", "../../sessions")
ESCALATIONS_FILE = os.getenv("ESCALATIONS_FILE", "../../escalations.json")


def sync_sessions(db: Session) -> None:
    """Scan sessions/ dirs not yet in call_records and insert them."""
    if not os.path.exists(SESSIONS_DIR):
        return

    existing_dirs = {r.session_dir for r in db.query(CallRecord).all()}

    for entry in os.scandir(SESSIONS_DIR):
        if not entry.is_dir() or entry.path in existing_dirs:
            continue

        transcript_path = os.path.join(entry.path, "transcript.json")
        if not os.path.exists(transcript_path):
            continue

        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        audio_path = os.path.join(entry.path, "audio.wav")

        record = CallRecord(
            session_dir=entry.path,
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            duration_seconds=data.get("duration", 0.0),
            language=data.get("language", "en"),
            transcript=data.get("history", []),
            escalated=data.get("escalated", False),
            outcome=data.get("outcome", "bot_handled"),
            cost_usd=data.get("cost_usd", 0.0),
            audio_path=audio_path if os.path.exists(audio_path) else None,
        )
        db.add(record)

    db.commit()


def sync_escalations(db: Session) -> None:
    """Scan escalations.json entries not yet in DB and insert them."""
    if not os.path.exists(ESCALATIONS_FILE):
        return

    try:
        with open(ESCALATIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            escalations = json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        return

    existing_count = db.query(EscalationTicket).count()
    new_escalations = escalations[existing_count:]

    if not new_escalations:
        return

    admin_agents = db.query(Agent).filter(Agent.role.in_(["admin", "senior_agent"])).all()

    for item in new_escalations:
        ticket = EscalationTicket(
            issue_summary=item.get("issue", "Unknown issue")[:500],
            status="open",
            conversation=item.get("conversation", []),
            created_at=datetime.fromisoformat(item["timestamp"]) if "timestamp" in item else datetime.utcnow(),
        )
        db.add(ticket)
        db.flush()

        for agent in admin_agents:
            notification = Notification(
                agent_id=agent.id,
                type="new_escalation",
                message=f"New escalation ticket #{ticket.id}: {ticket.issue_summary[:100]}",
            )
            db.add(notification)

    db.commit()


async def periodic_sync(interval: int = 30) -> None:
    """Async loop running both sync functions every interval seconds."""
    while True:
        db = SessionLocal()
        try:
            sync_sessions(db)
            sync_escalations(db)
        except Exception as e:
            print(f"Sync error: {e}")
        finally:
            db.close()
        await asyncio.sleep(interval)
