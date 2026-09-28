"""Offline runtime smoke check with external connections denied.

Starts the real FastAPI lifespan and validates local data/models, upload,
graph, report export, source citations and Observatory using an isolated DB.
No frozen-model evaluation or training is rerun. Exit 1 on any failure.
"""
import json
import ipaddress
import os
from pathlib import Path
import socket
import sys
import tempfile
import warnings
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


ORIGINAL_CONNECT = socket.socket.connect
ORIGINAL_GETADDRINFO = socket.getaddrinfo


def is_local(host):
    if host in ("localhost", b"localhost", None):
        return True
    try:
        return ipaddress.ip_address(host.decode() if isinstance(host, bytes) else host).is_loopback
    except ValueError:
        return False


def local_connect(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6) and not is_local(address[0]):
        raise RuntimeError("External network connection attempted during offline verification")
    return ORIGINAL_CONNECT(sock, address)


def local_getaddrinfo(host, *args, **kwargs):
    if not is_local(host):
        raise RuntimeError("External DNS resolution attempted during offline verification")
    return ORIGINAL_GETADDRINFO(host, *args, **kwargs)


def main():
    if not (ROOT / "dist/index.html").is_file():
        raise RuntimeError("Built frontend missing; run npm run build on the preparation host")
    # TestClient dispatches in-process ASGI calls. Loopback socket pairs are
    # permitted for asyncio itself; remote connections and DNS are denied.
    with tempfile.TemporaryDirectory(prefix="bitkaun-offline-") as storage:
        os.environ["BITKAUN_DATA_DIR"] = storage
        with patch.object(socket.socket, "connect", local_connect), patch.object(socket, "getaddrinfo", local_getaddrinfo):
            from sklearn.exceptions import InconsistentVersionWarning
            warnings.filterwarnings("error", category=InconsistentVersionWarning)
            from fastapi.testclient import TestClient
            from backend.app.main import app

            with TestClient(app) as client:
                checks = []
                for path in ("/", "/analytics", "/terminal", "/docs/introduction", "/docs", "/openapi.json", "/source/docs/OFFLINE_LINUX.md"):
                    response = client.get(path)
                    response.raise_for_status()
                    checks.append(path)
                for name in ("overview", "dataset", "performance", "features", "pipeline", "patterns"):
                    response = client.get(f"/api/observatory/{name}")
                    response.raise_for_status()
                    if response.json()["status"] != "available":
                        raise RuntimeError(f"Observatory {name}: {response.json().get('message')}")
                    checks.append(f"observatory:{name}")
                pair = client.get("/api/ingest/sample-pair")
                pair.raise_for_status()
                content = pair.json()
                uploaded = client.post("/api/ingest/correlate", files={
                    "ledger_file": ("ledger.csv", content["ledger_csv"], "text/csv"),
                    "network_file": ("network.csv", content["network_csv"], "text/csv"),
                })
                uploaded.raise_for_status()
                result = uploaded.json()
                if not result["matched_records"]:
                    raise RuntimeError("Sample pair produced no exact-ID matches")
                for analysis in result["scenario_results"]:
                    if analysis["analysis_status"] != "AVAILABLE":
                        raise RuntimeError(f"ML inference unavailable: {analysis['analysis_message']}")
                    if analysis.get("anomaly_score") is None:
                        raise RuntimeError(f"Anomaly inference unavailable: {analysis.get('anomaly_message')}")
                checks.append("upload:correlation-and-ml")
                scenario = result["scenario_results"][0]["scenario_id"]
                graph = client.get(f"/graph/{scenario}")
                graph.raise_for_status()
                if not graph.json().get("nodes"):
                    raise RuntimeError("Uploaded scenario graph is empty")
                checks.append("graph:uploaded-scenario")
                txid = next(row["txid"] for row in result["correlation_evidence"] if row["match_status"] == "MATCHED")
                report = client.get(f"/api/dossier/{txid}/html")
                report.raise_for_status()
                if "<html" not in report.text.lower():
                    raise RuntimeError("Dossier endpoint returned no HTML")
                checks.append("export:html-dossier")
            print(json.dumps({"status": "passed", "platform": sys.platform,
                              "python": sys.version.split()[0], "external_network": "denied",
                              "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
