"""
API Client for interacting with the BitKaun FastAPI backend (localhost:8000).
Wraps all endpoints documented in docs/API_CONTRACT.md.
"""

from typing import Any, Optional
import requests
from .render import error_panel

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
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

    def _request(self, method: str, path: str, params: Optional[dict] = None, json_body: Optional[dict] = None) -> Optional[dict]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.request(method, url, params=params, json=json_body, timeout=self.timeout)
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

    def get_scenario(self, scenario_id: str) -> Optional[dict]:
        """GET /scenarios/{scenario_id} - Forensic profile of a scenario cluster."""
        return self._request("GET", f"/scenarios/{scenario_id}")

    def get_taint(self, address: str, decay_rate: float = 0.85, max_depth: int = 5) -> Optional[dict]:
        """GET /taint - Forward dirty coin poisoning with FIFO decay."""
        return self._request("GET", "/taint", params={"seed_address": address, "decay_rate": decay_rate, "max_depth": max_depth})

    def get_flow(self, txid: Any) -> Optional[dict]:
        """GET /transaction/{txid}/flow - Sankey UTXO flow decomposition."""
        return self._request("GET", f"/transaction/{txid}/flow")

    def get_communities(self, scenario_id: str) -> Optional[dict]:
        """GET /graph/{scenario_id}/communities - Greedy modularity syndicate partitioning."""
        return self._request("GET", f"/graph/{scenario_id}/communities")

    def get_anomaly(self, scenario_id: str) -> Optional[dict]:
        """GET /anomaly/{scenario_id} - Isolation Forest anomaly score and metrics."""
        return self._request("GET", f"/anomaly/{scenario_id}")

    def search(self, query: str) -> Optional[dict]:
        """GET /search - Universal forensic search."""
        return self._request("GET", "/search", params={"q": query})

    def list_scenarios(self, prefix: Optional[str] = None, page: int = 1, page_size: int = 20) -> Optional[list]:
        """GET /scenarios - Paginated cluster directory."""
        params = {"page": page, "page_size": page_size}
        if prefix:
            params["prefix"] = prefix
        return self._request("GET", "/scenarios", params=params)

    def get_benchmark(self) -> Optional[dict]:
        """GET /eval/benchmark - Quantitative model evaluation scorecard."""
        return self._request("GET", "/eval/benchmark")

    def get_telemetry(self) -> Optional[dict]:
        """GET /stats - Global network and node infrastructure telemetry."""
        return self._request("GET", "/stats")

    def get_dossier(self, txid: Any) -> Optional[dict]:
        """GET /api/dossier/{txid} - System-generated confidential LEA summary."""
        return self._request("GET", f"/api/dossier/{txid}")

    def get_tor_profiler(self, txid: Any) -> Optional[dict]:
        """GET /api/intel/tor-profiler/{txid} - Timing entropy and evasion score."""
        return self._request("GET", f"/api/intel/tor-profiler/{txid}")

    def get_tor_summary(self) -> Optional[dict]:
        """GET /api/intel/tor-summary - Tor infrastructure summary."""
        return self._request("GET", "/api/intel/tor-summary")

    def ingest_sample(self, sample_type: str) -> Optional[dict]:
        """POST /api/ingest/sample/{sample_type} - Live synthetic model injection."""
        return self._request("POST", f"/api/ingest/sample/{sample_type}")

    def ingest_transaction(self, payload: dict) -> Optional[dict]:
        """POST /api/ingest/transaction - Live custom transaction ingestion."""
        return self._request("POST", "/api/ingest/transaction", json_body=payload)

    def ingest_file(self, file_path: Any) -> Optional[dict]:
        """POST /api/ingest/file - Upload and ingest single bulk file (CSV, JSON, XML)."""
        path = Path(file_path)
        if not path.exists():
            error_panel("File Not Found", f"File '{path}' does not exist.")
            return None
        url = f"{self.base_url}/api/ingest/file"
        try:
            with open(path, "rb") as f:
                resp = requests.post(url, files={"file": (path.name, f, "application/octet-stream")}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            error_panel("Connection Failed", f"Backend unreachable at {self.base_url}")
            return None
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = resp.json().get("detail", str(e))
            except Exception:
                detail = resp.text
            error_panel(f"HTTP {resp.status_code} Ingestion Error", detail)
            return None
        except Exception as e:
            error_panel("Ingest Error", str(e))
            return None


# Global singleton instance
client = BitKaunApiClient()
