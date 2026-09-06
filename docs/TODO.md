# Project Task Tracker & Roadmap — SIH PS146

> ### ⚠️ MANDATORY PRE-COMMIT PROTOCOL
> **Rule for Collaborators:** Update this file, root `TODO.md`, and `CHANGELOG.md` **before every commit**!
> 1. Check off completed items by replacing `[ ]` with `[x]`.
> 2. Add any newly identified bug fixes, refactors, or feature requests under the relevant section.
> 3. Summarize your completed changes in `CHANGELOG.md`.

---

## Team Roles & Ownership Matrix
- **P1, P2:** Frontend Developers (React, TypeScript, Three.js, Cytoscape, UI/UX)
- **P3:** Data Engineering (Dataset generation, schema integrity, `DATA_DICTIONARY.md`)
- **P4:** Graph Engineering (Heterogeneous graph modeling, typology heuristics, CIOH clustering)
- **P5:** ML & Explainability (Feature engineering, XGBoost, TreeSHAP, Isolation Forest)
- **P6:** Team Lead & Backend (FastAPI, database, offline WSL2/Linux packaging, system integration)

---

## 🚀 Immediate Pending Tasks (High Priority)

### 1. Presentation & Judging Deliverables (P1, P2, P6)
- [ ] **Final Presentation Deck (PPT):** Create compelling 10–12 slide deck covering Problem Statement (PS146), Dual-Layer Architecture, V7 Organic Synthetic Dataset, ML Benchmarks (AUC ~0.999), and Live Demo Walkthrough.
- [ ] **2-Minute Pitch Video / Demo Script:** Record crisp screen walkthrough demonstrating alert triage, 3D graph exploration, SHAP evidence drawer, and CIOH cluster inspection.
- [ ] **Judges FAQ / Defense Cheat Sheet:** Prepare answers on data leakage prevention (scenario-level splitting), offline air-gapped compliance, and why individual feature ablation was replaced by group ablation.

### 2. Frontend & UI Visualizer Polish (P1, P2)
- [x] **Blinking Green Rectangle Cursor Dynamic Caret Synchronization:** Fully resolved cursor detachment bug; green blinking rectangle (`.cli-cursor`) now dynamically tracks insertion caret index across arrow keys, clicks, typing, history recalls, and auto-completion with character inversion.
- [ ] **Deadlock Protocol Interactive Engine:** Implement the full `DEADLOCK_PROTOCOL.md` specification (hydraulic dual curtain drop, jaw-snap skull formation, Pac-Man exit, live mempool stream simulation, and dynamic red-skull mutation).
- [ ] **Export to PDF / Dossier Download:** Implement one-click PDF generation for the `/alerts/{id}/evidence` case dossier drawer so investigators can export official forensic case reports.
- [ ] **3D Graph Camera Auto-Focus:** When selecting an alert from the triage table, smoothly animate the Three.js camera to focus and zoom in on the primary suspect wallet node.
- [ ] **Dynamic ML Threshold Slider:** Add an interactive threshold control in the UI (default `0.50`) allowing analysts to tune precision vs. recall dynamically and view real-time alert count changes.
- [ ] **Live Telemetry Stream Widget:** Connect the `/stream` simulated WebSocket / SSE endpoint to a live ticker component on the dashboard showing real-time transaction ingestion.


### 3. Backend & System Engineering (P6)
- [ ] **Unified Startup Script (`run_all.bat` / `run_all.sh`):** Create single double-click launchers for Windows and Linux/WSL2 that concurrently start both FastAPI (port 8000) and Vite (port 5173).
- [ ] **Expanded Route Unit Tests:** Add automated test coverage in `tests/` for `/alerts`, `/alerts/{id}/evidence`, `/anomaly/{scenario_id}`, and `/taint` endpoints.
- [ ] **Optional Disk Persistence Cache:** For low-RAM evaluation machines (<8GB RAM), provide an optional SQLite/Parquet disk-backed mode to keep memory footprint under 500MB.

### 4. Machine Learning & Anomaly Refinements (P5)
- [ ] **Zero-Day Anomaly Clustering:** Group high-anomaly scenarios (Isolation Forest score > 75) that fail typology classification into emergent pattern clusters using HDBSCAN.
- [ ] **Model Fairness & Calibration Drift Check:** Validate Expected Calibration Error (ECE) across different transaction fee regimes and time spans.

---

## ✅ Completed Tasks (Reference)

### Data Engineering (P3)
- [x] Generated Version 7 Candidate synthetic dataset with organic, unbounded wallet pools.
- [x] Injected realistic ransomware campaigns leveraging CoinJoin mixers for cash-out.
- [x] Implemented 80/20 scenario-stratified train/test splits with 0% data leakage.
- [x] Validated schema and dictionary in `DATA_DICTIONARY.md`.

### Graph Engineering (P4)
- [x] Built heterogeneous graph constructor (Wallet, Transaction, IP) in NetworkX.
- [x] Implemented CIOH clustering (92,438 multi-input txs into 634,214 entity clusters).
- [x] Implemented structural candidate discovery for Peeling Chains, Layering, Mixing, and Ransomware.
- [x] Built multi-hop BFS pathfinder (`GET /trace`) and forward taint risk propagation (`GET /taint`).

### Machine Learning & Explainability (P5)
- [x] Engineered 46 non-leaking features across Amount, Temporal, Structural, Script, Network, and Graph families.
- [x] Trained binary XGBoost model achieving ROC-AUC `0.9989` and PR-AUC `0.9986`.
- [x] Trained multiclass XGBoost typology classifier achieving Weighted-F1 `0.9668`.
- [x] Integrated dual TreeSHAP explainers providing per-prediction local feature attributions.
- [x] Trained licit-only Isolation Forest producing normalized 0–100 anomaly scores.
- [x] Exported deterministic model weights, evaluation reports, and `MANIFEST_v7_candidate.json`.

### Backend & API (P6)
- [x] Developed high-throughput FastAPI application with 13 modular routers.
- [x] Built in-memory data indexing engine querying 294,693 transactions in sub-millisecond time.
- [x] Integrated ML candidate scoring filtering 1,282 candidates into 1,077 high-precision alerts.
- [x] Built offline compliance setup with local font embedding and cross-platform launchers.

### Frontend Dashboard (P1, P2)
- [x] Built cyber-themed Holmes Forensic Terminal with custom design system.
- [x] Implemented interactive 3D force-directed WebGL graph visualizer (`Three.js`) + Cytoscape link-analysis.
- [x] Fixed terminal character typewriter typing effect with blinking cursor, audio throttling, line-by-line reveal, and click-to-skip in `CliOutputRenderer.tsx`.
- [x] Overhauled 2D Graph Visualizer in `GraphCanvas.tsx`: replaced unbounded coordinate layout with organic bounded spring-relaxation, resolved microscopic zoom bug, implemented interactive Pan & Zoom controls HUD.
- [x] Transformed graph nodes into embossed Bitcoin medallion sprites with metallic rims, glowing halation rings, and tilted **₿** insignia.
- [x] Implemented dynamic trust/risk color taxonomy: Green (`#00ff66`, High Trust / Low Risk), Orange (`#ffaa00`, Medium Trust / Warning), Red (`#ff3344`, Low Trust / Threat).
- [x] Added dynamic SVG animated orbs traveling along directed transaction edges showing flow direction and transaction volume.
- [x] Pure 3D WebGL Three.js Graph Engine (`GraphCanvas.tsx`): 60 FPS hardware acceleration, zero lag, embossed Bitcoin medallion sprites, dynamic trust colors (Green, Orange, Red), and glowing directional transaction orbs.
- [x] Authentic Linux TTY Typewriter Engine (`CliOutputRenderer.tsx`): character-by-character stdout stream with blinking block cursor `▌`, throttled audio keyclicks, and instant skip.
- [x] Classic CLI ASCII Spinner (`CliSpinner.tsx`): rotating `/ - \ |` animation at 80ms across scenario loading and command execution.
- [x] Live `logs` Command: real-time streaming transaction batch querying `/api/stream/batch`.
- [x] Comprehensive Zero-Placeholder & Hardcode Purge: removed unused mock datasets, computed dynamic risk metrics, and enforced explicit `Feature not implemented` messaging.
- [x] Built ranked alert triage feed with severity indicators and typology filtering.
- [x] Created forensic evidence drawer showing SHAP feature attributions and telemetry breakdown.
- [x] Verified 100% offline functionality with zero external CDN dependencies.


