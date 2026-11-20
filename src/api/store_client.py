from __future__ import annotations

import httpx
from loguru import logger
from config.settings import STORE_API_URL, STORE_API_KEY


class StoreClient:
    def __init__(self):
        self.base_url = STORE_API_URL
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {STORE_API_KEY}"},
            timeout=10.0,
        )

    def search_products(self, query: str) -> list | None:
        """GET /products?query={query}. Returns None on error."""
        url = f"{self.base_url}/products"
        logger.info(f"API: search_products query='{query}'")
        try:
            response = self.client.get(url, params={"query": query})
            response.raise_for_status()
            logger.debug(f"search_products response: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"search_products error: {e}")
            return None

    def get_order(self, order_id: str) -> dict | None:
        """GET /orders/{order_id}. Returns None on error."""
        url = f"{self.base_url}/orders/{order_id}"
        logger.info(f"API: get_order id='{order_id}'")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            logger.debug(f"get_order response: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"get_order error: {e}")
            return None

    def get_billing(self, customer_id: str) -> dict | None:
        """GET /billing/{customer_id}. Returns None on error."""
        url = f"{self.base_url}/billing/{customer_id}"
        logger.info(f"API: get_billing id='{customer_id}'")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            logger.debug(f"get_billing response: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"get_billing error: {e}")
            return None

    def create_ticket(self, issue: str, conversation: list) -> dict | None:
        """POST /tickets. Returns None on error."""
        url = f"{self.base_url}/tickets"
        logger.info(f"API: create_ticket issue='{issue[:50]}...'")
        try:
            response = self.client.post(
                url,
                json={"issue": issue, "conversation": conversation},
            )
            response.raise_for_status()
            logger.debug(f"create_ticket response: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"create_ticket error: {e}")
            return None

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
