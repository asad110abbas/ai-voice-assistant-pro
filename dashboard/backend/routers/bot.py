from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
import sys
import tempfile
from datetime import datetime

import numpy as np
import soundfile as sf
from loguru import logger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.brain.memory import new_session_dir, save_transcript
from src.api.store_client import StoreClient
from src.abuse_guard import AbuseGuard
from src.multimodal.gemini_client import detect_language, clean_response

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_VOICE = os.getenv("GEMINI_LIVE_VOICE", "Aoede")
SILENCE_TIMEOUT = 30

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are Briha, an AI customer support assistant for an online electronics store. You support English, Urdu, and Roman Urdu. Always detect the language and reply in the same language. Do not use markdown, bullets, or special characters. Keep responses concise and suitable for speech.",
)

GREETING_TEXT = (
    "Assalamoalaikum! I am Briha AI Voice Assistant. "
    "Aap mujhse products ki price, orders, ya koi bhi query pooch sakte hain. "
    "If you would like to speak to a human agent, just say: transfer to agent. "
    "Agar aap hamare agent se baat karna chahte hain, toh bas bolein: agent ko transfer karo."
)

ESCALATION_MESSAGE = "I am transferring you to a support agent now. Please hold."

AGENT_TRANSFER_PHRASES = [
    'agent se baat', 'agent chahiye', 'insaan se baat', 'banda chahiye',
    'agent ko do', 'mujhe agent', 'human agent', 'real person',
    'speak to agent', 'talk to agent', 'transfer to agent',
    'representative chahiye', 'agent se milana',
]


def _pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    channels, bit_depth = 1, 16
    byte_rate = rate * channels * bit_depth // 8
    block_align = channels * bit_depth // 8
    data_size = len(pcm)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size, b'WAVE',
        b'fmt ', 16, 1, channels, rate,
        byte_rate, block_align, bit_depth,
        b'data', data_size,
    )
    return header + pcm


def _is_agent_request(text: str) -> bool:
    t = text.lower()
    return any(phrase in t for phrase in AGENT_TRANSFER_PHRASES)


async def tts_gemini(text: str) -> str | None:
    """Gemini 2.5 Flash TTS."""
    if not GEMINI_API_KEY:
        return None
    try:
        def _call():
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_TTS_MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=GEMINI_TTS_VOICE,
                            )
                        )
                    ),
                ),
            )
            return response.candidates[0].content.parts[0].inline_data.data

        pcm_data = await asyncio.to_thread(_call)
        wav_bytes = _pcm_to_wav(pcm_data)
        return base64.b64encode(wav_bytes).decode("utf-8")
    except Exception as e:
        logger.warning(f"Gemini TTS error: {e}")
        return None


async def tts_edge(text: str, lang: str = "English") -> str | None:
    """edge-tts fallback."""
    try:
        import edge_tts
        # Roman Urdu is Urdu written in Latin letters — an Urdu-script voice mispronounces
        # it badly, so it needs the English voice (which reads Latin script naturally).
        voice = "ur-PK-UzmaNeural" if lang == "Urdu" else "en-US-AriaNeural"
        communicate = edge_tts.Communicate(text, voice)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.warning(f"edge-tts error: {e}")
    return None


router = APIRouter()


def load_engine(api_client, session_dir):
    from src.multimodal.gemini_client import GeminiClient
    return GeminiClient(api_client, session_dir)


@router.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("Voice WebSocket connected")

    api_client = StoreClient()
    session_dir = new_session_dir()
    engine = load_engine(api_client, session_dir)
    abuse_guard = AbuseGuard("websocket_client")
    call_outcome = "bot_handled"

    try:
        # Greeting
        try:
            _init = await asyncio.wait_for(websocket.receive(), timeout=15)
            if _init.get("text"):
                d = json.loads(_init["text"])
                if d.get("type") == "ready":
                    audio_b64 = await tts_gemini(GREETING_TEXT) or await tts_edge(GREETING_TEXT, "Roman Urdu")
                    await websocket.send_json({
                        "type": "response",
                        "user_text": "",
                        "bot_text": GREETING_TEXT,
                        "audio_base64": audio_b64,
                    })
                    engine.conversation_history.append({"role": "assistant", "content": GREETING_TEXT})
                    engine._save()
                    logger.info("Greeting sent")
        except asyncio.TimeoutError:
            logger.warning("No ready signal — skipping greeting")
        except WebSocketDisconnect:
            logger.info("Client disconnected during greeting")
            return
        except Exception as e:
            logger.warning(f"Greeting error: {e}")

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=SILENCE_TIMEOUT)
            except asyncio.TimeoutError:
                call_outcome = "timeout"
                try:
                    await websocket.send_json({
                        "type": "timeout",
                        "bot_text": "No activity detected for 30 seconds. Goodbye!",
                    })
                except Exception:
                    pass
                break

            user_text = ""
            bot_text = ""
            detected_lang = "English"
            tmp_path = None

            # Text input
            if message["type"] == "websocket.receive" and message.get("text"):
                data = json.loads(message["text"])

                if data.get("type") == "ping":
                    continue

                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                if _is_agent_request(user_text):
                    call_outcome = "agent_transfer"
                    bot_text = ESCALATION_MESSAGE
                    engine.metadata["outcome"] = "agent_transfer"
                    engine.metadata["escalated"] = True
                    engine._save()
                    audio_b64 = await tts_gemini(bot_text) or await tts_edge(bot_text)
                    await websocket.send_json({
                        "type": "response",
                        "user_text": user_text,
                        "bot_text": bot_text,
                        "audio_base64": audio_b64,
                    })
                    break

                abuse_type = abuse_guard.check(user_text)
                if abuse_type:
                    call_outcome = "spam"
                    engine.metadata["outcome"] = "spam"
                    engine._save()
                    bot_text = "Your session has been terminated due to a policy violation."
                    audio_b64 = await tts_gemini(bot_text) or await tts_edge(bot_text)
                    await websocket.send_json({
                        "type": "response",
                        "user_text": user_text,
                        "bot_text": bot_text,
                        "audio_base64": audio_b64,
                    })
                    break

                bot_text, detected_lang = engine.chat_text(user_text)

            # Audio input
            elif message["type"] == "websocket.receive" and message.get("bytes"):
                audio_bytes = message["bytes"]
                if not audio_bytes:
                    continue
                logger.info(f"Audio received: {len(audio_bytes)} bytes")

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                try:
                    audio_array, sample_rate = sf.read(tmp_path, dtype="float32")
                    if audio_array.ndim > 1:
                        audio_array = audio_array[:, 0]
                    if len(audio_array) == 0:
                        await websocket.send_json({"type": "empty"})
                        continue

                    user_text, bot_text, detected_lang = engine.process(audio_array, sample_rate)

                    if user_text:
                        if _is_agent_request(user_text):
                            call_outcome = "agent_transfer"
                            engine.metadata["outcome"] = "agent_transfer"
                            engine._save()
                            bot_text = ESCALATION_MESSAGE
                            audio_b64 = await tts_gemini(bot_text) or await tts_edge(bot_text, detected_lang)
                            await websocket.send_json({
                                "type": "response",
                                "user_text": user_text,
                                "bot_text": bot_text,
                                "audio_base64": audio_b64,
                            })
                            break

                        abuse_type = abuse_guard.check(user_text)
                        if abuse_type:
                            call_outcome = "spam"
                            engine.metadata["outcome"] = "spam"
                            engine._save()
                            bot_text = "Your session has been terminated due to a policy violation."
                            audio_b64 = await tts_gemini(bot_text) or await tts_edge(bot_text)
                            await websocket.send_json({
                                "type": "response",
                                "user_text": user_text,
                                "bot_text": bot_text,
                                "audio_base64": audio_b64,
                            })
                            break
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            else:
                continue

            if not bot_text:
                await websocket.send_json({"type": "empty"})
                continue

            if ESCALATION_MESSAGE.lower() in bot_text.lower():
                call_outcome = "agent_transfer"

            logger.info(f"User: '{user_text}' | Bot: '{bot_text[:80]}'")
            audio_b64 = await tts_gemini(bot_text) or await tts_edge(bot_text, detected_lang)
            await websocket.send_json({
                "type": "response",
                "user_text": user_text,
                "bot_text": bot_text,
                "audio_base64": audio_b64,
            })

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        engine.metadata["outcome"] = call_outcome
        engine._save()
        logger.info(f"Call ended. Outcome: {call_outcome}")
