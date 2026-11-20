from __future__ import annotations

import json
import os
import time
from datetime import datetime
from difflib import SequenceMatcher
from loguru import logger
from config.settings import MAX_SESSION_DURATION, BLOCKLIST_FILE, ABUSE_LOG_FILE

PROFANITY_LIST = [
    # English
    "fuck", "shit", "bitch", "asshole", "bastard", "damn", "crap",
    "idiot", "stupid", "moron", "retard", "loser", "jerk",
    # Urdu / Roman Urdu
    "gandu", "madarchod", "behenchod", "bhen ki", "teri maa",
    "kuttay", "harami", "kameena", "suar", "ullu", "gadha",
    "chutiya", "bhosdi", "randi", "haramzada", "sala",
]

INJECTION_PHRASES = [
    "ignore previous instructions",
    "ignore all previous",
    "forget your instructions",
    "disregard previous",
    "jailbreak",
    "system prompt",
    "reveal your prompt",
    "show your instructions",
    "act as",
    "pretend you are",
    "you are now",
    "bypass",
    "override instructions",
    "do anything now",
    "dan mode",
    "developer mode",
]


class AbuseGuard:
    def __init__(self, ip: str):
        self.ip = ip
        self._session_messages: list[str] = []
        self._session_start = time.time()

    def check(self, user_text: str) -> str | None:
        """
        Returns abuse type string or None if clean.
        Types: 'offensive_language', 'spam', 'prompt_injection', 'session_timeout'
        """
        text_lower = user_text.lower()

        # Check offensive language
        for word in PROFANITY_LIST:
            if word in text_lower:
                logger.warning(f"Offensive language detected from {self.ip}: '{word}'")
                return "offensive_language"

        # Check prompt injection
        for phrase in INJECTION_PHRASES:
            if phrase in text_lower:
                logger.warning(f"Prompt injection detected from {self.ip}: '{phrase}'")
                return "prompt_injection"

        # Check session timeout
        elapsed = time.time() - self._session_start
        if elapsed > MAX_SESSION_DURATION:
            logger.warning(f"Session timeout for {self.ip}: {elapsed:.0f}s")
            return "session_timeout"

        # Check spam (3+ near-identical messages)
        self._session_messages.append(user_text)
        if len(self._session_messages) >= 3:
            recent = self._session_messages[-3:]
            similarities = []
            for i in range(len(recent)):
                for j in range(i + 1, len(recent)):
                    ratio = SequenceMatcher(None, recent[i], recent[j]).ratio()
                    similarities.append(ratio)
            if similarities and min(similarities) > 0.85:
                logger.warning(f"Spam detected from {self.ip}")
                return "spam"

        return None

    def block(self, ip: str, reason: str, transcript: list) -> None:
        """Append to blocklist.json and abuse_log.json."""
        timestamp = datetime.now().isoformat()

        # Update blocklist
        blocklist = []
        if os.path.exists(BLOCKLIST_FILE):
            try:
                with open(BLOCKLIST_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        blocklist = json.loads(content)
            except (json.JSONDecodeError, IOError):
                blocklist = []

        if not any(entry.get("ip") == ip for entry in blocklist):
            blocklist.append({"ip": ip, "reason": reason, "timestamp": timestamp})

        with open(BLOCKLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(blocklist, f, ensure_ascii=False, indent=2)

        # Update abuse log
        abuse_log = []
        if os.path.exists(ABUSE_LOG_FILE):
            try:
                with open(ABUSE_LOG_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        abuse_log = json.loads(content)
            except (json.JSONDecodeError, IOError):
                abuse_log = []

        abuse_log.append({
            "ip": ip,
            "reason": reason,
            "transcript": transcript,
            "timestamp": timestamp,
        })

        with open(ABUSE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(abuse_log, f, ensure_ascii=False, indent=2)

        logger.warning(f"IP blocked: {ip}, reason: {reason}")

    def is_blocked(self, ip: str) -> bool:
        """Returns True if IP is in blocklist.json."""
        if not os.path.exists(BLOCKLIST_FILE):
            return False
        try:
            with open(BLOCKLIST_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return False
                blocklist = json.loads(content)
                return any(entry.get("ip") == ip for entry in blocklist)
        except (json.JSONDecodeError, IOError):
            return False
