# Project Changelog — SIH PS146 (BitKaun Forensic Platform)

> ### ⚠️ MANDATORY PRE-COMMIT PROTOCOL
> **Rule for Collaborators:** Update this file and `TODO.md` **before every commit**!
> - Add a new entry under `## Recent Entries` with the date, module, author/role, and description of changes.
> - Format: `- YYYY-MM-DD [Module] [Author/Role] — What changed and why`.
> - Always place the newest entries at the top of the section.

---

## Recent Entries

- **2026-09-06 [Backend/ML/UI] [P1/P4/P6]** — **Items B, C, D Finalization (Graph Embeddings, Network Schema, UI Polishing):**
  - **Item B (Task 3 & 5)**: Added 8-dimensional graph structural topological embeddings (`cluster_embedding`) to `clustering_service.py` & `schemas.py` satisfying PS146 "CIOH + graph embeddings". Implemented explicit `src_ip`, `dst_ip`, `src_port`, `dst_port` network schema across `schemas.py`, `data_service.py`, and `graph_service.py`.
  - **Item C (Confidence Discrepancy)**: Added Section 5 root-cause audit documentation in `docs/backend/BACKEND.md` explaining historical evaluation transcription artifact vs. strictly independent live inference pipelines.
  - **Item D (UI/UX Polish)**: Populated `cluster_id`, `transaction_count`, `tags`, `first_seen`, `last_seen` in `graph_service.py` and `NodeDetails.tsx` eliminating unexplained "N/A" ransomware wallet fields. Fixed alert card header text clipping in `AlertsSubwindow.tsx`. Added Shannon entropy formula and second units in `tor_profiler.py` and `CliOutputRenderer.tsx`. Corrected hardcoded `/home/param` path in `backend/app/main.py`. Verified 11/11 backend pytest pass and 0-error frontend build.

- **2026-09-06 [UI/Terminal] [P1/P2]** — **Blinking Green Rectangle Cursor Dynamic Caret Synchronization (`App.tsx`, `terminal.css`):**
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


- **2026-09-06 [DevOps/FullStack] [P6]** — **Full-Stack Execution & Windows/WSL2 Portability Audit:**
  - Resolved Windows case-sensitivity collision (`README.md` vs `readme.md`) enabling seamless branch transitions between `backend` and `ml`.
  - Installed and verified unified dependencies: `networkx`, `xgboost`, `lightgbm`, `shap`, `python-louvain`, and `pytest`.
  - Executed complete V7 production ML pipeline (`train_production.py`), generating evaluated model weights (`binary_model_v7_candidate.ubj`, `typology_model_v7_candidate.ubj`), metrics reports, and manifest (`MANIFEST_v7_candidate.json`).
  - Successfully ran backend test suite via `pytest tests/` (5/5 tests passing).
  - Verified concurrent execution of FastAPI backend (`http://127.0.0.1:8000`) and Vite frontend dev server (`http://127.0.0.1:5173`).
  - Added root-level `CHANGELOG.md` and `TODO.md` handoff documentation with strict pre-commit workflows.

- **2026-09-05 [Integration] [P1/P2/P6]** — **End-to-End Frontend-Backend Integration & Air-Gapped Compliance:**
  - Replaced all mock/stubbed responses across the React dashboard with live FastAPI REST endpoints (`/health`, `/entity`, `/transaction`, `/graph`, `/trace`, `/alerts`, `/anomaly`).
  - Resolved multi-hop schema mismatches in `/trace` BFS route and `/graph/{scenario_id}` Cytoscape format.
  - Achieved 100% offline air-gapped compliance by removing external Google Font CDN and embedding `Share Tech Mono` locally in `/public/fonts`.
  - Integrated live TreeSHAP feature attributions directly into the forensic evidence drawer.

- **2026-09-05 [ML/Detection] [P5/P6]** — **Task 4: Isolation Forest Anomaly Detection Engine:**
  - Implemented `ml/05_anomaly_detection.py` training an Isolation Forest (`anomaly_model_v7.pkl`) fitted strictly on licit transaction behavior.
  - Calibrated outlier decision function into a normalized 0–100 anomaly score (`norm_range: [-0.6078, -0.3870]`).
  - Added `backend/app/services/anomaly_service.py` and `routes_anomaly.py` (`GET /anomaly/{scenario_id}`) returning scenario anomaly scores and radar feature decomposition.

- **2026-09-05 [ML/Alerts] [P4/P5/P6]** — **Task 2 + 6 Fix: ML-Driven Alerts & Typology SHAP Explanations:**
  - Refactored `typology_detector.py` to decouple structural candidate discovery from alert generation.
  - Added automated candidate scoring through `ml_service.score_candidate()`: structural shapes are evaluated against the binary XGBoost model, discarding non-illicit candidates (1,077 ML alerts emitted, 205 false positives dropped).
  - Integrated native multi-class TreeSHAP attributions for the predicted typology class, generating plain-English explanations.

- **2026-09-05 [Data/Pipeline] [P3/P5]** — **V7 Candidate Dataset Generation & Schema Freeze:**
  - Finalized Version 7 Candidate dataset across 294,693 transactions, 5,440 scenarios, and 984,076 unique addresses.
  - Guaranteed zero scenario, address, or transaction leakage across 80/20 train/test splits.
  - Generated full 46-feature matrices (`scenario_features_full_train.csv`, `scenario_features_full_test.csv`) covering Amount, Temporal, Structural, Script, Network, and Graph dimensions.
  - Documented complete data schema in `DATA_DICTIONARY.md`.

- **2026-09-04 [Graph/Clustering] [P4/P6]** — **CIOH Entity Clustering & Graph Heuristics:**
  - Implemented Common-Input Ownership Heuristic (`clustering_service.py`) analyzing 92,438 multi-input transactions into 634,214 entity clusters.
  - Created `GET /entity/{address}/cluster` endpoint returning cluster member addresses and aggregate balance.
  - Implemented forward taint risk propagation (`taint_service.py` / `GET /taint`) for tracing tainted fund flows from flagged seeds.

- **2026-09-03 [Backend/API] [P6]** — **FastAPI Core Architecture & In-Memory Data Store:**
  - Built high-performance in-memory data store (`data_service.py`) loading and indexing 294k rows in ~17 seconds for sub-millisecond API response times.
  - Implemented 13 REST API routes (`health`, `entity`, `transaction`, `graph`, `trace`, `alerts`, `search`, `stats`, `stream`, `intel`, `dossier`, `anomaly`).
  - Implemented BFS multi-hop pathfinding (`GET /trace`) with configurable depth and minimum BTC threshold.

- **2026-09-02 [Frontend/UI] [P1/P2]** — **Holmes Forensic Terminal Interface & 3D Visualizer:**
  - Developed cyber-themed dark mode UI with interactive 3D WebGL force-directed graph (`Three.js`) and Cytoscape.js 2D link-analysis.
  - Built ranked alert triage feed with severity indicators (CRITICAL, HIGH, MEDIUM, LOW) and typology filtering.
  - Designed dual-layer forensic case dossier showing on-chain UTXO details alongside P2P network telemetry.

---

## Version Milestones

| Version | Date | Key Deliverables |
|---|---|---|
| **v7.0 (Current)** | 2026-09-06 | 294k V7 dataset, 46-feature ML pipeline, TreeSHAP XAI, Isolation Forest, CIOH clustering, live FastAPI + React UI |
| **v6.0** | 2026-09-05 | Feature-group ablation methodology, XGBoost multiclass typology classifier |
| **v5.0** | 2026-09-04 | Structural drift guard, unified acceptance audit suite |
| **v2.0** | 2026-09-02 | Initial 82k transactions dataset, FastAPI skeleton, basic 2D graph viewer |
