# Frontend Dashboard & Visualizer Specification

> **Owners:** P1, P2 (Frontend Engineers & UI/UX)  
> **Source of Truth Reference:** [API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md)

---

## 1. Development Guidelines & Mock Data Strategy

> ### ⚡ IMMEDIATE DEVELOPMENT RULE
> Frontend development for P1 and P2 proceeds immediately using **mock data JSON fixtures** directly shaped after the response schemas in [API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md). **Do not wait for the live backend API to be deployed.**

---

## 2. Core Dashboard Components

The application is structured into four primary interactive views:

```text
src/
├── components/
│   ├── alerts/
│   │   ├── AlertTable.tsx          # Ranked forensic alert inbox with sorting and severity filters
│   │   ├── AlertCard.tsx           # Compact summary card for individual candidate alerts
│   │   └── AlertFilterBar.tsx      # Filter by pattern_type, confidence slider, date range
│   ├── graph/
│   │   ├── GraphVisualizer.tsx     # Cytoscape.js / vis.js interactive link-analysis canvas
│   │   ├── NodeDetailPopover.tsx   # Tooltip/flyout showing address or txid properties on hover/click
│   │   ├── GraphControls.tsx       # Zoom, pan, layout toggles (cose, breadthfirst, concentric)
│   │   └── GraphLegend.tsx         # Node type badges (Wallet, Transaction, IP) & edge colors
│   ├── evidence/
│   │   ├── EvidenceDrawer.tsx      # Slide-out forensic dossier for selected candidate
│   │   ├── ShapWaterfallChart.tsx  # Horizontal bar/waterfall chart of SHAP feature attributions
│   │   ├── TelemetryCard.tsx       # Dual-card display (On-chain financial vs Network telemetry)
│   │   └── ExportReportModal.tsx   # PDF / JSON forensic report export generator
│   └── common/
│       ├── Header.tsx              # System status, active scenario badge, offline mode indicator
│       └── StatCard.tsx            # High-level metrics (Total Alerts, High Risk Typologies, Monitored TXs)
├── mocks/
│   ├── mockAlerts.json             # Seeded from API_CONTRACT.md Section 2.4
│   ├── mockEvidence.json           # Seeded from API_CONTRACT.md Section 2.5
│   └── mockGraph.json              # Seeded from API_CONTRACT.md Section 2.3
└── services/
    └── api.ts                      # Axios / Fetch client switching between mock data and backend API
```

---

## 3. UI Component Behavior & API Mapping

| Component | API Route | Key Rendered Fields | Interactivity |
|---|---|---|---|
| **Alert Inbox** | `GET /alerts` | `candidate_id`, `predicted_pattern_type`, `confidence`, `severity`, `primary_wallet`, `detected_at` | Row click triggers graph focus and opens Evidence Drawer. Filter by minimum confidence score. |
| **Link-Analysis Graph** | `GET /graph/{scenario_id}` | Nodes (`Wallet`, `Transaction`, `IP`), Edges (`SENT`, `RECEIVED`, `BROADCAST`), `amount_btc`, `relay_timestamp` | Interactive physics/layout layout; drag, zoom, node highlight on click, hover tooltips. |
| **Evidence Dossier** | `GET /alerts/{id}/evidence` | `typology_heuristic_match`, `ml_feature_attributions` (SHAP), `telemetry_summary`, transactions list | Visual SHAP feature bars (Red for risk-increasing, Green for risk-decreasing); exportable forensic case file. |
| **Entity Inspector** | `GET /entity/{address}` | `is_licit_exchange`, `total_received_btc`, `total_sent_btc`, `tx_count` | Displays exchange badge and transaction history list for inspected address. |
| **Transaction Modal** | `GET /transaction/{txid}` | `input_addresses`, `output_addresses`, `amounts`, `fee_btc`, `node_type`, `country_code`, `asn`, `isp` | Displays dual on-chain vs network telemetry cards. |

---

## 4. Visual Node / Edge Encoding Rules

- **Nodes:**
  - `Wallet`: Hexagon / Circle icon. Default: Blue. Licit Exchange (`is_licit_exchange=true`): Cyan badge.
  - `Transaction`: Square / Box. Illicit Candidate: Red / Amber. Licit: Slate grey.
  - `IP`: Server / Globe icon. Tor / VPN / Bulletproof: Purple with caution ring. Residential: Dark green.
- **Edges:**
  - `SENT`: Directed arrow `Wallet → Tx` with thickness proportional to $\log(\text{amount\_btc})$.
  - `RECEIVED`: Directed arrow `Tx → Wallet` with thickness proportional to $\log(\text{amount\_btc})$.
  - `BROADCAST`: Dashed line `IP → Tx` displaying relay port and latency on hover.

---

## 5. Frontend Action Items & TODOs

- `[ ]` **[TODO: P1]** Implement mock data fixtures in `src/mocks/` matching `API_CONTRACT.md`.
- `[ ]` **[TODO: P1]** Build responsive dashboard frame with alert inbox table and filtering drawer.
- `[ ]` **[TODO: P2]** Configure Cytoscape.js / vis.js canvas with custom node stylings and auto-layout.
- `[ ]` **[TODO: P1/P2]** Build SHAP explanation bar chart component in the forensic evidence drawer.
- `[ ]` **[TODO: P1/P2]** Prepare presentation slide deck (PPT) with dashboard screenshots and system demo flow.
