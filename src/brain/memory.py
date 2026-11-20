import json
import os
from datetime import datetime
from loguru import logger


def new_session_dir() -> str:
    """Creates sessions/session_YYYYMMDD_HHMMSS/ and returns its path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join("sessions", f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    logger.info(f"New session directory created: {session_dir}")
    return session_dir


def save_transcript(history: list, metadata: dict, session_dir: str) -> None:
    """Writes transcript.json to the session directory."""
    transcript_path = os.path.join(session_dir, "transcript.json")
    data = {
        "history": history,
        "language": metadata.get("language", "en"),
        "escalated": metadata.get("escalated", False),
        "start_time": metadata.get("start_time", ""),
        "end_time": metadata.get("end_time", ""),
        "duration": metadata.get("duration", 0),
    }
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.debug(f"Transcript saved to {transcript_path}")


def load_transcript(session_dir: str) -> dict:
    """Reads transcript.json from the session directory. Returns empty dict if missing."""
    transcript_path = os.path.join(session_dir, "transcript.json")
    if not os.path.exists(transcript_path):
        logger.warning(f"Transcript not found: {transcript_path}")
        return {}
    with open(transcript_path, "r", encoding="utf-8") as f:
        return json.load(f)
