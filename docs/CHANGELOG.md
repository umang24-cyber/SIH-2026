# CHANGELOG

## Logging Rules
- Record one line per meaningful change.
- Newest entries must always be placed at the top.
- Required format: `YYYY-MM-DD [name] [module] — what changed`

---

## Entries

- 2026-09-03 [P6] [Backend] — Implemented in-memory data ingestion engine (`loader.py`, `parser.py`) loading 82,078 transactions, Pydantic v2 models (`schemas.py`), NetworkX graph serializer & BFS tracer, and FastAPI application (`main.py`) serving `/health`, `/entity`, `/transaction`, `/graph`, `/trace`, and `/alerts`. 7/7 automated unit tests passing.
- 2026-09-03 [P6] [Compliance] — Added `.gitattributes` enforcing UNIX LF line endings across repository; updated `API_CONTRACT.md` with `GET /trace` and `GET /health` specifications.
- 2026-09-03 [P6] [Docs] — Initialized project documentation suite (README, API_CONTRACT, ARCHITECTURE, TODO, SETUP, BACKEND, GRAPH, ML, FRONTEND, OFFLINE_LINUX_AUDIT).
- 2026-09-02 [P3] [Data] — DATA_DICTIONARY.md v2.0 finalized, 15/15 integrity checks passing.
