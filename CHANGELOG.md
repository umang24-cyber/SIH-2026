# Project Changelog — SIH PS146 (BitKaun Forensic Platform)

> ### ⚠️ MANDATORY PRE-COMMIT PROTOCOL
> **Rule for Collaborators:** Update this file and `TODO.md` **before every commit**!
> - Add a new entry under `## Recent Entries` with the date, module, author/role, and description of changes.
> - Format: `- YYYY-MM-DD [Module] [Author/Role] — What changed and why`.
> - Always place the newest entries at the top of the section.

---

## Recent Entries

- **2026-09-25 [Frontend/Docs/Navigation] [P1/P2/P6]** — **Editorial Landing Page & BitKaun Field Guide:**
  - Added an ivory, olive, and wine editorial theme with locally bundled fonts and interactive ASCII fern, wine glass, and Bitcoin artwork.
  - Implemented 15 handbook-backed documentation pages with local search, chapter/heading navigation, code-copy controls, and responsive layouts.
  - Added a book-page transition into the guide, reduced-motion and skip controls, terminal session continuity, and scoped production frontend routes while preserving FastAPI's API documentation.
  - Added browser-check infrastructure and a manual review checklist. Final `npm run build` passed; final browser verification is deferred to manual review at the user's request.
  - Ignored the local chat-context Markdown file.

- **2026-09-08 [ML/Backend/Frontend] [P1/P2/P5/P6]** — **Complete V8 Migration & Enhanced Dual-Stream (Ledger + Telemetry) Correlation Dashboard:**
  - **ML V8 Standardization (`MANIFEST_v8.json`, `models/`, `train_v8.py`)**: Established official `MANIFEST_v8.json` declaring the 46-feature contract across 5,440 scenarios (294,639 transactions). Standardized `binary_model_v8.ubj`, `typology_model_v8.ubj`, and `anomaly_model_v8.pkl`. Updated `ml/train_v8.py` to auto-resolve data directories and save `_v8` artifacts.
  - **Backend V8 & Satoshi Accounting Normalization (`config.py`, `ml_service.py`, `anomaly_service.py`, `parser.py`, `routes_ingest.py`)**: Updated API engine version to `8.0.0` and expected rows to `294,639`. Wired `ml_service.py` and `anomaly_service.py` directly to V8 models and manifests. Added satoshi-to-BTC scale normalization in `normalize_transaction_dict` and `parse_and_enrich_dataframe` (converting $>21\text{M}$ satoshi values to standard BTC), eliminating astronomical amounts like 72M BTC in ransomware scenarios.
  - **Enhanced Dual-Stream Upload & Correlation Dashboard (`TwoStreamUploadView.tsx`, `CliOutputRenderer.tsx`, `App.tsx`)**: Upgraded dual-stream ingestion for Stream 1 (Blockchain Ledger) and Stream 2 (P2P Network Telemetry). Added 1-click `[⚡ Load Sample Dual-Stream Pair]` demo preset for instant testing. Overhauled the post-correlation result screen into a comprehensive forensic dossier surfacing outer-join match telemetry, V8 ML risk gauges, calibrated typology confidence, Isolation Forest anomaly outlier detection (0–100), TreeSHAP risk factors, and interactive `[🌐 Open in 3D Graph]` buttons.
  - **CLI & Banner Versioning (`App.tsx`, `CliOutputRenderer.tsx`, `cli/bitkaun_cli/__init__.py`)**: Synchronized CLI and web terminal shell to `v8.0.0` / `BitKaun v8.0 Forensic Engine`, adding `correlate` and `dualstream` command aliases.

- **2026-09-07 [UI/3D/Terminal] [P1/P2]** — **3D Graph True Screen-Space Panning, Balanced Node Spacing & Concurrent Command Execution:**
  - **3D Screen-Space Panning (`GraphCanvas.tsx`)**: Added true perspective screen-space panning with 1:1 mouse tracking. Supports Middle-Click Drag, Right-Click Drag, Shift + Left-Click Drag, and an interactive `[MODE: PAN / REVOLVE]` toolbar toggle button. Added drag distance detection (`dragDist > 6`) so pan and rotation drags never trigger unintended node clicks.
  - **Balanced Node Spacing & Fog Overhaul (`GraphCanvas.tsx`)**: Re-calibrated graph cluster radius dynamically with node count (`baseRadius = Math.max(90, Math.min(260, 65 + sqrt(N) * 6.5))`), set `initialCamZ` to frame the whole cluster on load, and replaced pitch-black exponential fog with far linear fog (`Fog(0x020603, 1200, 4500)`). Nodes, edges, and labels are now 100% visible, bright, and clearly positioned without scattering into the void.
  - **Concurrent Command Execution With Active Graph (`App.tsx`)**: Enabled typing and running arbitrary CLI commands (`alerts`, `status`, `tor`, `inspect`, `trace`, `help`, etc.) seamlessly while the 3D graph visualizer remains active on screen. Added global keyboard autofocus redirection to the input prompt with `{ preventScroll: true }`, ensuring investigators can type anytime without losing their viewport position.
  - **Duplicate Graph Guard (`App.tsx`)**: If `graph` is entered when a graph is already active on screen, the system safely updates the scenario (e.g. `graph licit_00001`) or notifies the user without re-mounting duplicate WebGL contexts.


- **2026-09-07 [UI/CLI/Backend/Stability] [P1/P2/P6]** — **CLI Command Rate Limiting & 3D WebGL Multi-Context Crash Prevention:**
  - **3D Graph Cooldown & Singleton Context (`App.tsx`)**: Enforced a 1.5-second cooldown on `graph` command execution with informative countdown warnings. Enforced a singleton active Three.js WebGL canvas in the DOM by automatically closing/cleaning up prior graph instances, eliminating multiple concurrent WebGL animation loops, memory leaks, and tab crashes.
  - **Burst Command Rate Limiter (`App.tsx`)**: Added a global burst throttle in `handleRunCommand` restricting rapid input bursts (>8 commands per 2 seconds) to protect terminal stability.
  - **Backend & Python CLI Throttling (`routes_graph.py`, `graph.py`)**: Added sliding-window rate limiting on `GET /graph/{scenario_id}` (max 12 requests per 3 seconds returning HTTP 429) and a 1.0s client-side cooldown in Python CLI `graph.py`.

- **2026-09-07 [UI/3D/ML/Backend] [P1/P2/P6]** — **SHAP Window Clipping Fix, 3D Graph Node Spacing Expansion, Terminal Input Wrapping, Click-Snap Prevention & Parameter Wiring:**
  - **SHAP & Node Details Window Layout (`NodeDetails.tsx`, `GraphView.tsx`)**: Fixed vertical layout clipping; positioned container below the top header with `max-height: calc(100% - 68px)`, `overflow-y: auto`, `box-sizing: border-box`, and `word-break: break-word`. Added explicit `[✕ CLOSE]` dismissal button and bound click event stopPropagation.
  - **3D Graph Node Density & Spacing Refactor (`GraphCanvas.tsx`)**: Replaced cramped fixed-radius sphere with dynamic multi-shell Fibonacci radial distribution scaling with $\sqrt{N}$ (`baseRadius = Math.max(160, sqrt(N) * 36)`). Added $O(N)$ spatial grid-binning collision repulsion ensuring guaranteed minimum spacing between nodes, scaled medallion sprites based on node count, and widened camera zoom boundaries (`camera.position.z` max scale up to $2.6\times$).
  - **Terminal Long Input Word-Wrapping (`terminal.css`, `App.tsx`)**: Fixed horizontal overflow where long unbroken text strings extended past the window edge. Set `.terminal-body` to `overflow-x: hidden`, updated `.prompt-line` and `.input-cursor-wrapper` with `word-break: break-all; overflow-wrap: anywhere; white-space: pre-wrap;`, and ensured typed characters and inline cursor wrap naturally to next line.
  - **Window Snapping to Lowest Point on Click Fix (`App.tsx`)**: Resolved frustrating scroll snap where clicking 3D canvas, nodes, controls, or subwindows called `.focus()` on the bottom input and jumped the scrollbar. Added `handleTerminalWindowClick` with `target.closest(...)` ignore checks and passed `{ preventScroll: true }` to all `.focus()` invocations.
  - **Backend Parameter Connection & Hardcode Purge (`graph_service.py`, `GraphView.tsx`, `NodeDetails.tsx`, `ForensicDashboard.tsx`, `App.tsx`)**: Connected previously "N/A" parameters: transaction amount (BTC), miner fee, input count, output count, cluster IDs, pattern tags, IP relay ASN, ISP, infrastructure type, and network latency directly from live backend records. Embedded scenario TreeSHAP feature attributions directly inside `NodeDetails.tsx` and dynamically wired `ForensicDashboard` to `/alerts/{id}/evidence`. Replaced static `inspect` risk scores with live ML scenario analysis queries.

- **2026-09-07 [Frontend/UI/CLI Integration] [P1/P2/P6]** — **Live Alerts Integration & Deep SHAP Evidence Dossiers (Aligned with Python CLI):**
  - **Live Backend API Alignment**: Replaced hardcoded alerts in `AlertsSubwindow.tsx` and `ForensicDashboard.tsx` with dynamic fetches from `GET /alerts`. Enhanced `src/services/api.ts` with `EvidenceResponse`, `FeatureAttribution`, and pattern filter support in `getAlerts`.
  - **CLI Reference Implementation in Web UI**: Adapted `cli/bitkaun_cli/commands/alerts.py` into the frontend terminal shell (`App.tsx` and `CliOutputRenderer.tsx`). Added full support for `alerts [--detail <candidate_id>]`, `alerts -d <candidate_id>`, `alerts <candidate_id>`, and direct `cand_<id>` execution.
  - **Prioritized Alerts Feed (`AlertsListView.tsx`)**: Created modular alerts feed displaying active monitored count vs top displayed, live typology filter pills (ALL, RANSOMWARE, PEELING_CHAIN, LAYERING, MIXING), severity threat dividers, calibrated binary & typology confidence, and quick action buttons (`[🔍 SHAP Evidence]`, `[🌐 3D Graph]`, `[👤 Inspect Wallet]`).
  - **Deep SHAP Evidence Dossier View (`AlertDetailView.tsx`)**: Built comprehensive forensic dossier viewer surfacing XGBoost/TreeSHAP feature attributions with impact scores & risk direction badges (`▲ ELEVATES RISK` / `▼ LOWERS RISK`), heuristic corroboration status, and P2P origin telemetry (IPs, ASNs, countries, infrastructure nodes).

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
