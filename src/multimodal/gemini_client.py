import io
import os
import re
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
import numpy as np
import soundfile as sf
from loguru import logger

from config.settings import (
    GEMINI_API_KEY,
    MAX_CONVERSATION_HISTORY,
    SYSTEM_PROMPT,
)
from src.api.store_client import StoreClient
from src.brain.escalation import UnresolvedTurnCounter, is_escalation, log_escalation
from src.brain.memory import load_transcript, save_transcript
from src.brain.rag import get_retriever

ROMAN_URDU_STRONG = {
    'kya', 'hai', 'hain', 'nahi', 'nhi', 'nahin', 'mujhe', 'muje',
    'aap', 'tou', 'toh', 'aur', 'hoga', 'hogi', 'karo', 'karna',
    'batao', 'yaar', 'bhai', 'kahan', 'kuch', 'sab', 'woh', 'wo',
    'iska', 'uska', 'apna', 'apni', 'humara', 'tumhara', 'mera', 'meri',
    'chahiye', 'chahye', 'milega', 'milegi', 'dou', 'dedo', 'krdo',
    'krna', 'krdou', 'hogya', 'hogyi', 'hua', 'hui', 'aye', 'aya',
    'puchhna', 'poochna', 'btao', 'btayen', 'price', 'kimat', 'daam',
    'kitna', 'kitni', 'order', 'deliver', 'refund', 'wapas',
    'agent', 'transfer', 'insaan', 'banda', 'representative',
}

ROMAN_URDU_WEAK = {
    'main', 'ka', 'ki', 'ke', 'se', 'mein', 'pe', 'par', 'tha', 'thi',
    'ho', 'bhi', 'or', 'ji', 'sahab', 'lena', 'dena', 'jana', 'aana',
}

AGENT_TRANSFER_PHRASES = [
    'agent se baat', 'agent chahiye', 'insaan se baat', 'banda chahiye',
    'representative chahiye', 'human agent', 'real person', 'speak to agent',
    'talk to agent', 'transfer to agent', 'mujhe agent', 'agent ko do',
]


def detect_language(text: str) -> str:
    urdu_chars = sum(1 for c in text if '؀' <= c <= 'ۿ')
    if urdu_chars > len(text) * 0.15:
        return "Urdu"
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if words & ROMAN_URDU_STRONG:
        return "Roman Urdu"
    if len(words & ROMAN_URDU_WEAK) >= 2:
        return "Roman Urdu"
    return "English"


def get_lang_hint(lang: str) -> str:
    if lang == "Urdu":
        return (
            "CRITICAL LANGUAGE RULE: Reply in Roman Urdu only (Urdu written in English letters). "
            "CORRECT: 'Aap ka order kal tak pahunch jaye ga.' "
            "WRONG: 'آپ کا آرڈر کل تک پہنچ جائے گا' "
            "No Urdu script. Write exactly as Pakistanis type on WhatsApp."
        )
    if lang == "Roman Urdu":
        return (
            "CRITICAL LANGUAGE RULE: Reply in Roman Urdu only (Urdu written in English letters). "
            "CORRECT: 'Aap ka order kal tak pahunch jaye ga. Koi aur help chahiye?' "
            "WRONG: 'آپ کا آرڈر' or mixing Urdu script. "
            "Write naturally as Pakistanis type on WhatsApp — friendly, professional Roman Urdu."
        )
    return (
        "CRITICAL LANGUAGE RULE: Reply in fluent, professional English only. "
        "No Urdu script, Roman Urdu, or mixed languages."
    )


FOREIGN_SCRIPT_RE = re.compile(r'[一-鿿぀-ヿ가-힯]+')


def clean_response(text: str) -> str:
    return FOREIGN_SCRIPT_RE.sub('', text).strip()


TOOL_USAGE_INSTRUCTION = (
    "You have tools available: get_order_status, get_billing_info, search_products, "
    "search_faq. Only call get_order_status if the customer has given an order ID. Only call "
    "get_billing_info if the customer has given a customer ID. If the customer clearly asks about "
    "an order, delivery, refund, shipment, or billing status but has NOT given an order ID or "
    "customer ID, do not call any tool — ask them to share their order ID or customer ID instead. "
    "Never guess or invent order/billing details. For product price or availability questions, use "
    "search_products. For general questions, use search_faq if it might have a relevant answer."
)

AUDIO_LANGUAGE_INSTRUCTION = (
    "CRITICAL LANGUAGE RULE: First determine what language the customer is speaking in the audio — "
    "English, Urdu, or Roman Urdu (Urdu written in English letters, e.g. 'Aap kaise hain'). Reply in "
    "that exact same language and script. If the customer speaks Roman Urdu, reply in Roman Urdu only "
    "— never in Urdu script. Never switch languages."
)

AUDIO_RESPONSE_FORMAT = (
    "Respond in EXACTLY this format, nothing else:\n"
    "TRANSCRIPT: <exact words the customer said in the audio, transcribed as-is>\n"
    "REPLY: <your spoken response to the customer — concise, no markdown, bullets, or special characters>"
)

ESCALATION_MESSAGE = "I am transferring you to a support agent now. Please hold."
GEMINI_MODEL = "gemini-flash-latest"

# Cost rates (USD)
GEMINI_AUDIO_COST_PER_MIN = 0.001
GEMINI_OUTPUT_COST_PER_1K_CHARS = 0.0003


class GeminiClient:
    def __init__(self, api_client: StoreClient, session_dir: str):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.api_client = api_client
        self.session_dir = session_dir
        self.retriever = get_retriever()
        self.turn_counter = UnresolvedTurnCounter()
        self.metadata = {
            "language": "en",
            "escalated": False,
            "outcome": "bot_handled",
            "cost_usd": 0.0,
            "start_time": datetime.now().isoformat(),
            "end_time": "",
            "duration": 0,
        }
        self._start_time = datetime.now()
        existing = load_transcript(session_dir)
        self.conversation_history = existing.get("history", [])
        if existing.get("language"):
            self.metadata["language"] = existing["language"]
        logger.info("PO Bot ready — Gemini 2.0 Flash direct audio")

    def _build_history_text(self) -> str:
        if not self.conversation_history:
            return ""
        lines = []
        for turn in self.conversation_history[-10:]:
            role = "Customer" if turn["role"] == "user" else "Bot"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)

    def _build_tools(self):
        """Gemini function-calling tools, bound to this session's API client and FAQ retriever.

        Passing plain Python callables lets the SDK's automatic function calling execute them
        and fold the whole order/billing/product/FAQ lookup into the same generate_content turn,
        instead of a separate pre-call regex/API-lookup pass.
        """

        def get_order_status(order_id: str) -> str:
            """Look up an order's status, items, and delivery details by order ID."""
            logger.info(f"Tool call: get_order_status({order_id})")
            result = self.api_client.get_order(order_id)
            return str(result) if result is not None else "Store API error: could not retrieve order information."

        def get_billing_info(customer_id: str) -> str:
            """Look up a customer's billing, invoice, and payment information by customer ID."""
            logger.info(f"Tool call: get_billing_info({customer_id})")
            result = self.api_client.get_billing(customer_id)
            return str(result) if result is not None else "Store API error: could not retrieve billing information."

        def search_products(query: str) -> str:
            """Search the store's product catalog for price and availability by product name or keyword."""
            logger.info(f"Tool call: search_products({query})")
            result = self.api_client.search_products(query)
            return str(result) if result is not None else "Store API error: could not search products."

        def search_faq(query: str) -> str:
            """Search the store's frequently-asked-questions knowledge base for a matching answer."""
            logger.info(f"Tool call: search_faq({query})")
            return self.retriever.retrieve(query, n_results=5) or "No matching FAQ found."

        return [get_order_status, get_billing_info, search_products, search_faq]

    def _parse_transcript_reply(self, raw: str) -> tuple[str, str]:
        if "REPLY:" not in raw:
            return "", raw
        before, _, after = raw.partition("REPLY:")
        reply = after.strip()
        transcript = before.split("TRANSCRIPT:", 1)[-1].strip() if "TRANSCRIPT:" in before else ""
        return transcript, reply

    def _call_gemini_audio(self, audio_array: np.ndarray, sample_rate: int) -> tuple[str, float, str]:
        """Single Gemini call: transcribe + tool-use (order/billing/product/FAQ) + reply, all merged.

        Returns (response_text, audio_seconds, user_text).
        """
        try:
            buf = io.BytesIO()
            sf.write(buf, audio_array, sample_rate, format="WAV")
            audio_bytes = buf.getvalue()
            audio_seconds = len(audio_array) / sample_rate
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")

            history_text = self._build_history_text()
            prompt_parts = []
            if history_text:
                prompt_parts.append(f"Previous conversation:\n{history_text}\n")
            prompt_parts.append(audio_part)
            prompt_parts.append(f"{AUDIO_LANGUAGE_INSTRUCTION}\n{TOOL_USAGE_INSTRUCTION}\n{AUDIO_RESPONSE_FORMAT}")

            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt_parts,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=self._build_tools(),
                    max_output_tokens=1024,
                ),
            )

            raw = (response.text or "").strip()
            user_text, bot_text = self._parse_transcript_reply(raw)
            return bot_text, audio_seconds, user_text

        except Exception as e:
            logger.error(f"Gemini audio error: {e}")
            raise

    def _call_gemini_text(self, user_text: str) -> str:
        """Text-only chat with Gemini, with order/billing/product/FAQ tools available."""
        history_text = self._build_history_text()
        parts = []
        if history_text:
            parts.append(f"Previous conversation:\n{history_text}\n")

        lang = detect_language(user_text)
        parts.append(get_lang_hint(lang))
        parts.append(TOOL_USAGE_INSTRUCTION)
        parts.append(f"\nCustomer says: {user_text}")

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=self._build_tools(),
                max_output_tokens=1024,
            ),
        )
        return (response.text or "").strip()

    def process(self, audio_array: np.ndarray, sample_rate: int) -> tuple:
        """Direct audio → Gemini → response. Returns (user_text, bot_text, lang)."""
        try:
            bot_response, audio_seconds, user_text = self._call_gemini_audio(audio_array, sample_rate)
        except Exception as e:
            return ("", self._escalate(f"Audio error: {e}"), "en")

        if not bot_response:
            return ("", "", "en")

        bot_response = clean_response(bot_response)
        lang = detect_language(bot_response)

        # Cost tracking
        cost = (audio_seconds / 60) * GEMINI_AUDIO_COST_PER_MIN
        cost += (len(bot_response) / 1000) * GEMINI_OUTPUT_COST_PER_1K_CHARS
        self.metadata["cost_usd"] = round(self.metadata.get("cost_usd", 0.0) + cost, 6)

        return self._finalize(user_text, bot_response, lang)

    def chat_text(self, user_text: str) -> tuple:
        """Text input → Gemini → response. Returns (bot_text, lang)."""
        try:
            bot_response = self._call_gemini_text(user_text)
        except Exception as e:
            logger.error(f"Gemini text error: {e}")
            return (self._escalate(f"Chat error: {e}"), "en")

        if not bot_response:
            return (self._escalate("Gemini returned an empty response."), "en")

        bot_response = clean_response(bot_response)
        lang = detect_language(user_text)

        cost = (len(bot_response) / 1000) * GEMINI_OUTPUT_COST_PER_1K_CHARS
        self.metadata["cost_usd"] = round(self.metadata.get("cost_usd", 0.0) + cost, 6)

        _, result, detected_lang = self._finalize(user_text, bot_response, lang)
        return (result, detected_lang)

    def _finalize(self, user_text: str, bot_response: str, lang: str) -> tuple:
        store_key = os.getenv("STORE_API_KEY", "")
        has_store_api = store_key and store_key != "your-store-api-key"

        if is_escalation(bot_response):
            log_escalation(bot_response, self.conversation_history)
            if has_store_api:
                self.api_client.create_ticket(bot_response, self.conversation_history)
            self.metadata["escalated"] = True
            self.metadata["outcome"] = "agent_transfer"
            bot_response = bot_response + " " + ESCALATION_MESSAGE

        if user_text:
            self.conversation_history.append({"role": "user", "content": user_text})
        self.conversation_history.append({"role": "assistant", "content": bot_response})

        max_items = MAX_CONVERSATION_HISTORY * 2
        if len(self.conversation_history) > max_items:
            self.conversation_history = self.conversation_history[-max_items:]

        self._save()
        logger.info(f"Bot [{lang}]: '{bot_response[:80]}'")
        return (user_text, bot_response, lang)

    def _escalate(self, reason: str) -> str:
        logger.warning(f"Escalating: {reason}")
        log_escalation(reason, self.conversation_history)
        store_key = os.getenv("STORE_API_KEY", "")
        if store_key and store_key != "your-store-api-key":
            self.api_client.create_ticket(reason, self.conversation_history)
        self.metadata["escalated"] = True
        self.metadata["outcome"] = "agent_transfer"
        self._save()
        return ESCALATION_MESSAGE

    def _save(self):
        now = datetime.now()
        self.metadata["end_time"] = now.isoformat()
        self.metadata["duration"] = (now - self._start_time).total_seconds()
        save_transcript(self.conversation_history, self.metadata, self.session_dir)
