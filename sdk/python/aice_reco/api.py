# aice_reco/api.py
import requests
from aice_reco.exceptions import APIError, ConnectionError


class APIClient:
    """
    Handles all HTTP communication with the FastAPI endpoint.
    Called by tracker.py — clients never use this directly.
    """

    def __init__(self, api_key: str, api_url: str, timeout: int = 5):
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            "Content-Type":  "application/json",
            "X-API-Key":     api_key
        }

    def send_event(self, payload: dict) -> dict:
        """
        POST a single event to /api/v1/events.
        Returns the response dict on success.
        Raises APIError or ConnectionError on failure.
        """
        url = f"{self.api_url}/events"

        try:
            response = requests.post(
                url,
                json    = payload,
                headers = self.headers,
                timeout = self.timeout
            )

            # 200 — success
            if response.status_code == 200:
                return response.json()

            # 422 — validation error from FastAPI
            if response.status_code == 422:
                detail = response.json().get('detail', 'Validation error')
                raise APIError(422, str(detail))

            # 500 — server error
            if response.status_code == 500:
                raise APIError(500, "Internal server error")

            # anything else
            raise APIError(
                response.status_code,
                response.text
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to API at {url}. "
                f"Is the server running?"
            )

        except requests.exceptions.Timeout:
            raise ConnectionError(
                f"Request timed out after {self.timeout}s. "
                f"API may be slow or unreachable."
            )

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Unexpected request error: {str(e)}")

    def health_check(self) -> dict:
        """
        GET /api/v1/health to confirm API is reachable.
        Returns health status dict.
        """
        url = f"{self.api_url}/health"

        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            raise APIError(response.status_code, "Health check failed")

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to API at {url}."
            )