import json
import os
from datetime import datetime
from loguru import logger
from config.settings import ESCALATION_KEYWORDS, MAX_UNRESOLVED_TURNS, ESCALATIONS_FILE


def is_escalation(text: str) -> bool:
    """Returns True if text contains any escalation keyword (case-insensitive)."""
    text_lower = text.lower()
    for keyword in ESCALATION_KEYWORDS:
        if keyword.lower() in text_lower:
            logger.debug(f"Escalation keyword detected: '{keyword}'")
            return True
    return False


def log_escalation(issue: str, conversation: list, path: str = None) -> None:
    """Append escalation entry to escalations.json."""
    if path is None:
        path = ESCALATIONS_FILE

    entry = {
        "timestamp": datetime.now().isoformat(),
        "issue": issue,
        "conversation": conversation,
    }

    existing = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)
        except (json.JSONDecodeError, IOError):
            existing = []

    existing.append(entry)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    logger.info(f"Escalation logged to {path}")


class UnresolvedTurnCounter:
    def __init__(self):
        self._count = 0

    def increment(self) -> None:
        self._count += 1
        logger.debug(f"Unresolved turn count: {self._count}")

    def reset(self) -> None:
        self._count = 0
        logger.debug("Unresolved turn counter reset")

    def should_escalate(self) -> bool:
        return self._count >= MAX_UNRESOLVED_TURNS
