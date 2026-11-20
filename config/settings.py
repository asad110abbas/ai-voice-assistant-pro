import os
from dotenv import load_dotenv

load_dotenv()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))

# Store API
STORE_API_URL = os.getenv("STORE_API_URL", "https://api.example-store.com")
STORE_API_KEY = os.getenv("STORE_API_KEY", "")

# Session limits
MAX_SESSION_DURATION = int(os.getenv("MAX_SESSION_DURATION", "600"))

# File paths
ESCALATIONS_FILE = os.getenv("ESCALATIONS_FILE", "escalations.json")
BLOCKLIST_FILE = "blocklist.json"
ABUSE_LOG_FILE = "abuse_log.json"

# System prompt
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are Briha, a bilingual AI customer support assistant for an online electronics store. You assist customers in English, Urdu, and Roman Urdu. Always respond formally and helpfully. Do not use markdown, bullets, or special characters in your responses as they will be spoken aloud. If you cannot resolve an issue after multiple attempts, transfer the customer to a human agent."
)

# Escalation config
MAX_UNRESOLVED_TURNS = 3
ESCALATION_KEYWORDS = [
    # English
    "transfer",
    "escalate",
    "cannot resolve",
    "human agent",
    "speak to agent",
    "talk to agent",
    "real person",
    "customer service",
    # Urdu / Roman Urdu
    "agent chahiye",
    "transfer karein",
    "agent se baat",
    "insaan se baat",
    "support agent",
    "help chahiye",
]
