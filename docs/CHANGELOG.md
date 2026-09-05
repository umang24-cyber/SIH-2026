# CHANGELOG

## Logging Rules
- Record one line per meaningful change.
- Newest entries must always be placed at the top.
- Required format: `YYYY-MM-DD [name] [module] — what changed`

---

## Entries

- 2026-09-05 [P6/P1/P2] [Integration] — Completed full end-to-end frontend-backend integration. Replaced all mock data with real API calls to FastAPI backend. Fixed schema mismatches in multi-hop `/trace` route. Verified 100% offline air-gapped compliance by embedding 'Share Tech Mono' font locally. Validated ML Typology engine output and memory index sizes loading dynamically into the CLI.

- 2026-09-03 [P6] [Backend] — Implemented transaction flow decomposition (`/transaction/{txid}/flow`), NetworkX syndicate community detection (`/graph/{id}/communities`), deep scenario risk profiling (`/scenarios/{id}`), and offline quantitative benchmark evaluation (`/eval/benchmark`). All 15 unit test suites passing in 7.8s.
- 2026-09-03 [P6] [Backend] — Implemented Common-Input Ownership Heuristic (CIOH) clustering (`clustering_service.py`) analyzing 24,179 multi-input transactions into 244,363 entity clusters (`GET /entity/{address}/cluster`); implemented forward taint risk propagation (`taint_service.py` / `GET /taint`); created plug-and-play offline ML model hook (`ml_service.py`) with zero-leakage feature extraction.
- 2026-09-03 [P6] [Backend] — Built algorithmic typology detection engine (`typology_detector.py`) auto-identifying 23,646 candidate alerts (peeling chains, layering, mixing, ransomware); implemented universal forensic search (`/search`), cluster explorer (`/scenarios`), network telemetry statistics (`/stats/telemetry`), and case dossier export (`/alerts/{id}/export`).
- 2026-09-03 [P6] [Backend] — Implemented in-memory data ingestion engine (`loader.py`, `parser.py`) loading 82,078 transactions, Pydantic v2 models (`schemas.py`), NetworkX graph serializer & BFS tracer, and FastAPI application (`main.py`) serving `/health`, `/entity`, `/transaction`, `/graph`, `/trace`, and `/alerts`.
- 2026-09-03 [P6] [Compliance] — Added `.gitattributes` enforcing UNIX LF line endings across repository; added POSIX `run_backend.sh` and Windows `run_backend.bat` launchers.
- 2026-09-03 [P6] [Docs] — Initialized project documentation suite (README, API_CONTRACT, ARCHITECTURE, TODO, SETUP, BACKEND, GRAPH, ML, FRONTEND, OFFLINE_LINUX_AUDIT, SIH_PS146_Project_Plan.docx).
- 2026-09-02 [P3] [Data] — DATA_DICTIONARY.md v2.0 finalized, 15/15 integrity checks passing.
