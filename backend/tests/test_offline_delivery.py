"""Offline runtime routes and doc/source links use only shipped local assets."""
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_api_docs_reference_has_no_external_asset_urls():
    response = client.get("/docs")
    assert response.status_code == 200
    text = response.text
    assert "fetch('/openapi.json')" in text
    assert "https://" not in text
    assert "http://" not in text
    assert "cdn." not in text
    assert client.get("/redoc", follow_redirects=False).headers["location"] == "/docs"
    assert client.get("/openapi.json").status_code == 200


def test_local_source_citations_and_asset_isolation():
    source = client.get("/source/docs/OFFLINE_LINUX.md")
    assert source.status_code == 200
    assert "Linux offline delivery" in source.text
    assert client.get("/source/src/App.tsx").status_code == 200
    for path in ("/source/.git/config", "/source/ml/models/binary_model_v8.ubj", "/source/ml/models/anomaly_norm_params.json", "/source/data/processed/scenario_labels_test.csv", "/source/missing.md", "/source/%2e%2e/%2e%2e/secrets.md"):
        assert client.get(path).status_code == 404


def test_built_frontend_and_deep_links_have_one_local_origin():
    root = client.get("/")
    if not (Path(__file__).resolve().parents[2] / "dist/index.html").exists():
        assert root.status_code == 200 and root.json()["status"] == "ONLINE"
        return
    assert root.status_code == 200
    assert "src=\"/assets/" in root.text
    assert client.get("/analytics").status_code == 200
    assert client.get("/terminal").status_code == 200
    assert client.get("/docs/introduction").status_code == 200
    assert client.get("/api/observatory/overview").status_code == 200


def test_linux_launcher_has_no_online_install_or_dev_server():
    root = Path(__file__).resolve().parents[2]
    script = (root / "run_ubuntu.sh").read_text(encoding="utf-8")
    assert "pip install" not in script
    assert "npm run dev" not in script
    assert "--host 127.0.0.1" in script
    installer = (root / "scripts/install_offline.sh").read_text(encoding="utf-8")
    assert "PIP_NO_INDEX=1" in installer
    assert "--no-index" in installer
