import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.api.store_client import StoreClient
import src.multimodal.gemini_client as gc


@pytest.fixture
def mock_api_client():
    client = MagicMock(spec=StoreClient)
    client.search_products.return_value = [{"name": "Galaxy A55", "price": 100000}]
    client.get_order.return_value = {"status": "shipped"}
    client.create_ticket.return_value = {"ticket_id": 2}
    return client


@pytest.fixture
def sample_audio():
    return np.zeros(16000, dtype=np.float32), 16000


@pytest.fixture
def make_client(mock_api_client, tmp_path, monkeypatch):
    """Build a GeminiClient with the Gemini SDK and the RAG retriever mocked out."""
    monkeypatch.chdir(tmp_path)  # escalation logs are written to the working directory
    monkeypatch.setenv("STORE_API_KEY", "test-key")

    def _make(bot_text: str | None = None, error: Exception | None = None):
        with patch.object(gc.genai, "Client", return_value=MagicMock()), \
             patch.object(gc, "get_retriever", return_value=MagicMock()):
            client = gc.GeminiClient(mock_api_client, str(tmp_path))
        if error is not None:
            client._call_gemini_audio = MagicMock(side_effect=error)
        else:
            client._call_gemini_audio = MagicMock(return_value=(bot_text, 1.0, "user question"))
        return client

    return _make


def test_process_returns_text_response(make_client, sample_audio):
    client = make_client("The price of the Galaxy A55 is 100,000 rupees.")
    user_text, bot_text, lang = client.process(*sample_audio)
    assert user_text == "user question"
    assert isinstance(bot_text, str) and "100,000" in bot_text
    assert client.metadata["escalated"] is False
    assert client.metadata["cost_usd"] > 0


def test_escalation_detection_creates_ticket(make_client, mock_api_client, sample_audio):
    client = make_client("I need to transfer you to a human agent.")
    _, bot_text, _ = client.process(*sample_audio)
    mock_api_client.create_ticket.assert_called()
    assert client.metadata["escalated"] is True
    assert gc.ESCALATION_MESSAGE in bot_text


def test_model_failure_triggers_escalation(make_client, sample_audio):
    client = make_client(error=RuntimeError("network down"))
    _, bot_text, _ = client.process(*sample_audio)
    assert "transferring" in bot_text.lower()
    assert client.metadata["outcome"] == "agent_transfer"
