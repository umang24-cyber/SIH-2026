"""
API Client for interacting with the BitKaun FastAPI backend (localhost:8000).
Wraps all endpoints documented in docs/API_CONTRACT.md.
"""

from typing import Any, Optional
import requests
from .render import error_panel

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30.0  # seconds



class APIClientError(Exception):
    """Base exception for BitKaun API errors."""
    pass


class BackendConnectionError(APIClientError):
    """Raised when the backend cannot be reached."""
    pass


class BitKaunApiClient:
    """Thin HTTP client wrapping BitKaun AML backend endpoints."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, params: Optional[dict] = None) -> Optional[dict]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.request(method, url, params=params, timeout=self.timeout)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            error_panel(
                "Connection Failed",
                f"Backend unreachable at [bold underline]{self.base_url}[/bold underline] — is the FastAPI server running?\n"
                "[dim]Ensure 'python -m uvicorn backend.app.main:app --port 8000' is started.[/dim]"
            )
            return None
        except requests.exceptions.Timeout:
            error_panel(
                "Request Timeout",
                f"Request to {url} timed out after {self.timeout}s."
            )
            return None
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                err_data = resp.json()
                detail = err_data.get("detail", str(err_data))
            except Exception:
                detail = resp.text
            error_panel(
                f"HTTP {resp.status_code} Error",
                f"Endpoint returned error: {detail or str(e)}"
            )
            return None
        except Exception as e:
            error_panel("API Client Error", f"Unexpected error: {str(e)}")
            return None

    def get_health(self) -> Optional[dict]:
        """GET /health - System telemetry, loaded transaction count, clusters, uptime."""
        return self._request("GET", "/health")

    def get_entity(self, address: str) -> Optional[dict]:
        """GET /entity/{address} - Address metadata, transaction counts, exchange flag."""
        return self._request("GET", f"/entity/{address}")

    def get_transaction(self, txid: Any) -> Optional[dict]:
        """GET /transaction/{txid} - Detailed on-chain transaction UTXO data & network metadata."""
        return self._request("GET", f"/transaction/{txid}")

    def get_graph(self, scenario_id: str) -> Optional[dict]:
        """GET /graph/{scenario_id} - Graph nodes (Wallet, Tx, IP) and edges."""
        return self._request("GET", f"/graph/{scenario_id}")

    def get_trace(self, src: str, dst: str) -> Optional[dict]:
        """GET /trace?src=&dst= - Multi-hop shortest path between source & destination."""
        return self._request("GET", "/trace", params={"src": src, "dst": dst})

    def get_alerts(self, limit: int = 50) -> Optional[dict]:
        """GET /alerts - Prioritized list of forensic candidate alerts with ML predictions."""
        return self._request("GET", "/alerts", params={"limit": limit})

    def get_alert_evidence(self, candidate_id: str) -> Optional[dict]:
        """GET /alerts/{candidate_id}/evidence - Deep forensic evidence dossier and SHAP values."""
        return self._request("GET", f"/alerts/{candidate_id}/evidence")


# Global singleton instance
client = BitKaunApiClient()
