import pytest
import httpx
from unittest.mock import MagicMock, patch
from src.api.store_client import StoreClient


@pytest.fixture
def client():
    return StoreClient()


def test_search_products_happy_path(client):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"name": "iPhone 15", "price": 200000}]
    mock_response.raise_for_status.return_value = None

    with patch.object(client.client, "get", return_value=mock_response):
        result = client.search_products("iPhone 15")

    assert result == [{"name": "iPhone 15", "price": 200000}]


def test_get_order_happy_path(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"order_id": "ORD123", "status": "delivered"}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.client, "get", return_value=mock_response):
        result = client.get_order("ORD123")

    assert result == {"order_id": "ORD123", "status": "delivered"}


def test_get_billing_happy_path(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"customer_id": "CUST001", "balance": 5000}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.client, "get", return_value=mock_response):
        result = client.get_billing("CUST001")

    assert result == {"customer_id": "CUST001", "balance": 5000}


def test_create_ticket_happy_path(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ticket_id": 42, "status": "open"}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.client, "post", return_value=mock_response):
        result = client.create_ticket("Cannot resolve billing issue", [])

    assert result == {"ticket_id": 42, "status": "open"}


def test_search_products_returns_none_on_error(client):
    with patch.object(client.client, "get", side_effect=httpx.HTTPError("Connection error")):
        result = client.search_products("test")
    assert result is None


def test_get_order_returns_none_on_error(client):
    with patch.object(client.client, "get", side_effect=httpx.HTTPError("Not found")):
        result = client.get_order("INVALID")
    assert result is None


def test_get_billing_returns_none_on_error(client):
    with patch.object(client.client, "get", side_effect=httpx.HTTPError("Server error")):
        result = client.get_billing("INVALID")
    assert result is None


def test_create_ticket_returns_none_on_error(client):
    with patch.object(client.client, "post", side_effect=httpx.HTTPError("Server error")):
        result = client.create_ticket("issue", [])
    assert result is None
