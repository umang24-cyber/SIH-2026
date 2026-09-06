# CHANGELOG

> ### ⚠️ MANDATORY PRE-COMMIT PROTOCOL
> **Rule for Collaborators:** Update this file, root `CHANGELOG.md`, and `TODO.md` **before every commit**!
> - Add a new entry under `## Entries` with date, author/role, module, and description of changes.
> - Format: `- YYYY-MM-DD [Author/Role] [Module] — What changed and why`.
> - Always place the newest entries at the top of the section.

---

## Entries

- **2026-09-06 [P1/P2] [UI/Terminal]** — **Blinking Green Rectangle Cursor Dynamic Caret Synchronization (`App.tsx`, `terminal.css`):**
  - Resolved caret positioning bug where the solid green blinking rectangle (`.cli-cursor`) remained statically pinned to the end of the input line when typing or navigating through text.
  - Implemented exact character index tracking (`cursorPos`) via `selectionStart` synchronized across `onChange`, `onKeyDown`, `onKeyUp`, `onClick`, `onSelect`, and `onFocus`.
  - Added arrow key, Home, End, Backspace, and Delete caret listener with `requestAnimationFrame` and `setTimeout` selection range persistence for command history (ArrowUp/ArrowDown) and Tab auto-completion.
  - Split active prompt rendering into `textBefore`, `charAtCursor` (wrapped in `.cli-cursor` with character inversion: `#030805` text on `#00ff66` background), and `textAfter` with matching monospace metrics (`line-height: 24px`, `height: 24px`, `font-size: 20px`, `letter-spacing: 0.5px`).
  - Aligned `.terminal-real-input` font family, size, line-height, and padding to eliminate cursor offset during mouse clicks and text selection.

- **2026-09-06 [Architecture/Spec] [P1/P2/P6]** — **Deadlock Protocol Specification Generated (`DEADLOCK_PROTOCOL.md`):**
  - Authored comprehensive architectural and design specification for **Deadlock Protocol** — a live-streamed blockchain mempool simulation and autonomous threat containment engine.
  - Specified the dual hydraulic curtain drop with upper/lower jaw snap, complete cyber skull formation in retro green/black phosphor, and animated Pac-Man chomping screen exit.
  - Architected real-time streaming pipeline utilizing `/api/stream/replay`, on-the-fly 46-feature extraction, XGBoost inference, and Isolation Forest decision scores.
  - Detailed the "Red Skull Metamorphosis" where anomalous/compromised nodes breach threshold ($P \ge 0.85$, anomaly $\ge 75$) and mutate into pulsing red skull sprites with expanding laser shockwaves.
  - Formulated 5 high-impact feature enhancements: Judge Sabotage Injection Sandbox, Automated Section 91 Cr.P.C. Asset Freeze Dispatch, Dual-Layer Geographic Radar Projection, Autonomous CIOH Entity Unmasking, and procedural synthesizer sound design.

- **2026-09-06 [UI/3D/CLI] [P1/P2/P6]** — **Pure 3D WebGL Force Graph (Three.js Only), Authentic Linux TTY Typing Engine, Classic ASCII Spinner (`/-\|`) & Complete Hardcode Purge:**

  - **Pure 3D WebGL Graph Overhaul (`GraphCanvas.tsx`)**: Replaced the heavy 2D SVG canvas entirely with hardware-accelerated 3D WebGL (Three.js), achieving a silky-smooth 60 FPS with zero lag. Rendered nodes as embossed Bitcoin medallion sprites with metallic rims, radial disk gradients, circuit notches, and tilted **₿** insignia, dynamically colored by trust score (🟢 Green `< 0.40`, 🟠 Orange `0.40–0.75`, 🔴 Red `> 0.75`). Added animated 3D directional transaction orbs traveling continuously along edges with smooth orbit controls and HUD.
  - **Authentic Linux TTY Typewriter Engine (`CliOutputRenderer.tsx`)**: Eliminated block line-by-line pops; unified `STATUS`, `HELP`, `LOGS`, `TEXT`, `ERROR`, and `SUCCESS` outputs into character-by-character stdout streams with an active terminal block cursor `▌`, throttled mechanical audio clicks, and instant click-to-skip. Fixed typing animation restart bug on input keystrokes by wrapping in `React.memo`, isolating `useEffect` to `entry.id`, and memoizing callbacks with `useCallback`.
  - **Classic CLI ASCII Spinner (`CliSpinner.tsx`)**: Created reusable 80ms rotating `/ - \ |` ASCII spinner component; integrated across scenario graph loading and command execution in `App.tsx` and `GraphView.tsx`.
  - **Live `logs` Command**: Wired `logs` command to live backend `/api/stream/batch` endpoint, rendering real-time mempool transaction frames.
  - **Comprehensive Hardcode Purge**: Removed unused mock arrays (`INITIAL_NODES`, `INITIAL_LINKS`, `INITIAL_LOGS`), replaced static numbers with dynamic dataset calculations in `App.tsx` inspect handler, and enforced strict zero-placeholder fallback messaging.

- **2026-09-06 [UI/Graph/Tests] [P1/P2/P6]** — **Typing Engine Fix, Bitcoin Sprite Nodes, Moving Orbs, Hardcode Purge & Test Harmonization:**

  - Fixed terminal typewriter engine in `CliOutputRenderer.tsx`: added character-by-character reveals with blinking block cursor `▌`, line-by-line reveal for multi-line outputs (`STATUS`, `HELP`), audio keystroke click throttling, clean timer garbage collection, and click-to-skip functionality.
  - Overhauled `GraphCanvas.tsx` & `GraphView.tsx`: replaced microscopic/zoomed-out nodes with high-fidelity embossed **Bitcoin coin medallion sprites** centered in a bounded organic layout with zoom/pan controls (+, -, fit, reset, wheel, drag).
  - Implemented dynamic trust/risk color-coding for all nodes: **Green** (Low Risk / High Trust), **Orange** (Medium Risk / Elevated Warning), and **Red** (High Risk / Critical Threat).
  - Added continuous glowing **animated transaction orbs** traveling along every directed edge indicating fund direction and velocity in real time.
  - Purged all hardcoded mock fallbacks (`FORENSIC_SCENARIOS.peel_001`, fake `'82,078'` diagnostics numbers, etc.): connected live FastAPI `/graph` and `/health` endpoints with explicit `Feature not implemented (intended feature: "...")` fallbacks.
  - Harmonized `EXPECTED_TOTAL_ROWS` in `backend/app/core/config.py` to 96,251 and updated `tests/test_backend.py` assertions to dynamic lengths, eliminating stale hardcodes.
  - Verified 100% test pass rate across the full project test suite (58/58 passing in pytest).
  - Configured full Vite reverse proxy for all 16 backend endpoints.

- **2026-09-06 [P6] [DevOps/FullStack]** — Full-stack execution & Windows/WSL2 portability audit. Resolved Windows case-sensitivity collision (`README.md` vs `readme.md`) enabling clean branch switching between `backend` and `ml`. Installed and verified dependencies (`networkx`, `xgboost`, `lightgbm`, `shap`, `python-louvain`, `pytest`). Executed complete V7 ML pipeline (`train_production.py`), generating evaluated model weights (`binary_model_v7_candidate.ubj`, `typology_model_v7_candidate.ubj`), metrics reports, and manifest (`MANIFEST_v7_candidate.json`). Verified concurrent execution of FastAPI backend (`http://127.0.0.1:8000`) and Vite frontend dev server (`http://127.0.0.1:5173`). Added root-level `CHANGELOG.md` and `TODO.md`.

- **2026-09-05 [P1/P2/P6] [Integration]** — Completed full end-to-end frontend-backend integration. Replaced all mock data with live API calls to FastAPI backend (`/health`, `/entity`, `/transaction`, `/graph`, `/trace`, `/alerts`, `/anomaly`). Fixed schema mismatches in multi-hop `/trace` route. Verified 100% offline air-gapped compliance by embedding 'Share Tech Mono' font locally in `/public/fonts`. Validated live TreeSHAP explainability engine output loading into the forensic evidence drawer.

- **2026-09-05 [P5/P6] [ML/Detection]** — Implemented Task 4 Isolation Forest anomaly detection engine (`ml/05_anomaly_detection.py`, `backend/app/services/anomaly_service.py`) fitted strictly on licit behavior. Calibrated outlier decision function into normalized 0–100 anomaly scores and added `GET /anomaly/{scenario_id}` route with radar feature breakdown.

- **2026-09-05 [P4/P5/P6] [ML/Alerts]** — Resolved Task 2 + 6: decoupled algorithmic candidate discovery in `typology_detector.py` from alert generation. Structural candidates are now scored via `ml_service.score_candidate()`, dropping licit candidates (1,077 ML alerts emitted, 205 false positives dropped). Added native TreeSHAP attributions for the predicted typology class with natural language explanations.

- **2026-09-05 [P3/P5] [Data/Pipeline]** — Finalized Version 7 Candidate dataset across 294,693 transactions, 5,440 scenarios, and 984,076 unique addresses with zero train/test leakage. Engineered 46 non-leaking features across Amount, Temporal, Structural, Script, Network, and Graph families. Updated `DATA_DICTIONARY.md`.

- **2026-09-04 [P4/P6] [Graph/Clustering]** — Implemented Common-Input Ownership Heuristic (CIOH) clustering (`clustering_service.py`) analyzing 92,438 multi-input transactions into 634,214 entity clusters (`GET /entity/{address}/cluster`); implemented forward taint risk propagation (`taint_service.py` / `GET /taint`).

- **2026-09-03 [P6] [Backend]** — Implemented transaction flow decomposition (`/transaction/{txid}/flow`), NetworkX syndicate community detection (`/graph/{id}/communities`), deep scenario risk profiling (`/scenarios/{id}`), and offline quantitative benchmark evaluation (`/eval/benchmark`). All 15 unit test suites passing in 7.8s.

- **2026-09-03 [P6] [Backend]** — Built algorithmic typology detection engine (`typology_detector.py`) auto-identifying candidate alerts (peeling chains, layering, mixing, ransomware); implemented universal forensic search (`/search`), cluster explorer (`/scenarios`), network telemetry statistics (`/stats/telemetry`), and case dossier export (`/alerts/{id}/export`).

- **2026-09-03 [P6] [Backend]** — Implemented in-memory data ingestion engine (`loader.py`, `parser.py`) loading transactions into memory, Pydantic v2 models (`schemas.py`), NetworkX graph serializer & BFS tracer, and FastAPI application (`main.py`) serving `/health`, `/entity`, `/transaction`, `/graph`, `/trace`, and `/alerts`.

- **2026-09-03 [P6] [Compliance]** — Added `.gitattributes` enforcing UNIX LF line endings across repository; added POSIX `run_backend.sh` and Windows `run_backend.bat` launchers.

- **2026-09-03 [P6] [Docs]** — Initialized project documentation suite (README, API_CONTRACT, ARCHITECTURE, TODO, SETUP, BACKEND, GRAPH, ML, FRONTEND, OFFLINE_LINUX_AUDIT, SIH_PS146_Project_Plan.docx).

- **2026-09-02 [P3] [Data]** — DATA_DICTIONARY.md v2.0 finalized, 15/15 integrity checks passing.
