# 📟 BitKaun CLI — Bitcoin AML Forensics Investigation Terminal

> **Package Name:** `bitkaun`  
> **Interface Type:** Standalone Interactive REPL & One-Shot CLI Client  
> **Backend Target:** `http://localhost:8000` (FastAPI Forensic In-Memory Engine)  
> **Compliance:** 100% Air-Gapped / Offline Compliant · Zero External Network or CDN Calls  

---

## 1. Overview

`bitkaun` is a dedicated, production-grade command-line interface for the **BitKaun AML Forensics Platform**. Built using Python, `rich`, and `requests`, it operates as a second first-class client alongside the web terminal, communicating directly with the existing FastAPI backend via standard REST endpoints documented in `docs/API_CONTRACT.md`.

Just like `git` or `claude`, once installed, typing `bitkaun` in any terminal drops the investigator directly into a persistent, retro-cyber phosphor-green forensic REPL session (`bitkaun@investigation:~$ `). It can also execute one-shot commands directly from your system shell.

---

## 2. Installation & Quickstart

### Prerequisites
- Python 3.9+
- Backend running locally on `http://localhost:8000`

### Step 1: Start the Backend (if not already running)
From the project root:
```bash
python -m uvicorn backend.app.main:app --port 8000
```
Verify backend telemetry: `curl http://localhost:8000/health`

### Step 2: Install the CLI in Editable Mode
Navigate into the `cli` folder and install:
```bash
cd cli
pip install -e .
```
This registers the console script `bitkaun` in your environment's PATH.

### Step 3: Launch
```bash
# Launch interactive REPL session
bitkaun

# Or execute a one-shot command directly
bitkaun status
```

---

## 3. Architecture & File Structure

```
/cli
├── pyproject.toml              # Setuptools console script entry point: bitkaun = "bitkaun_cli.main:run"
├── requirements.txt            # Core dependencies (rich, requests)
├── README.md                   # Installation, usage guide, and command reference
└── bitkaun_cli/
    ├── __init__.py             # Package version
    ├── main.py                 # Terminal REPL loop, banner, signal handlers, shlex parser
    ├── api_client.py           # Thin HTTP wrapper with graceful connection error boundaries
    ├── render.py               # Rich phosphor-green console themes, boxes, panels, and badges
    └── commands/
        ├── __init__.py
        ├── status.py           # Queries /health -> system telemetry panel & metric grid
        ├── inspect.py          # Queries /entity/{addr} or /transaction/{txid} -> UTXO dossier
        ├── graph.py            # Queries /graph/{scenario_id} -> node/edge census & ASCII flow tree
        ├── trace.py            # Queries /trace?src=&dst= -> multi-hop path steps & typology badges
        ├── alerts.py           # Queries /alerts & /alerts/{id}/evidence -> ranked feed & SHAP table
        └── help_cmd.py         # Static command reference and syntax index
```

---

## 4. Forensic Command Reference

### `status`
Displays runtime system health, loaded transaction count, unique tracked wallets, CIOH cluster census, and ML model status.

```bash
bitkaun@investigation:~$ status
```

**Example Output:**
```
╭──────────────── [*] BITKAUN SYSTEM TELEMETRY & ENGINE STATUS ────────────────╮
│  BitKaun AML Forensics API  v2.0.0                                           │
│  Status:  ONLINE    Uptime: 15m 32s   Target: http://localhost:8000          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────┬────────────────────────┬────────────────────╮
│ Telemetry Metric               │          Value / State │ Forensic Scope     │
├────────────────────────────────┼────────────────────────┼────────────────────┤
│ Ledger Transactions            │                294,699 │ Master on-chain    │
│ Tracked Wallets                │                984,092 │ Distinct Base58    │
│ CIOH Clusters                  │                634,229 │ Co-owned clusters  │
│ Investigative Scenarios        │                  5,443 │ Crime syndicates   │
│ Prioritized Alerts             │                  1,105 │ ML-ranked alerts   │
│ ML Forensics Engine            │  ACTIVE (XGBoost + IF) │ Typology Class     │
│ Network Engine                 │         100% OFFLINE   │ Zero cloud calls   │
╰────────────────────────────────┴────────────────────────┴────────────────────╯
```

---

### `inspect <address | txid>`
Deep forensic inspection. Automatically detects whether the input is a Bitcoin Base58 wallet address or a 64-bit transaction ID.

#### Inspecting a Wallet Address:
```bash
bitkaun@investigation:~$ inspect 1jLgHKBTV4wPz8zugRhGrKfs6qcs
```
**Output:** Renders a wallet activity dossier with lifetime transaction count, total BTC received/sent, estimated net balance, first/last seen timestamps, exchange tags, and associated crime scenarios.

#### Inspecting a Transaction ID:
```bash
bitkaun@investigation:~$ inspect 187888339
```
**Output:** Renders transaction metadata, P2P network telemetry (origin relay IP, port, country, ASN, ISP, node type, and propagation delta), and a formatted UTXO input-to-output financial balance table.

---

### `graph <scenario_id>`
Retrieves scenario subgraph data and renders an intuitive ASCII structural tree and component census in the terminal.

```bash
bitkaun@investigation:~$ graph ransomware_03287
```

**Example Output:**
```
╭─────────────────── [*] SCENARIO ON-CHAIN TOPOLOGY SUMMARY ───────────────────╮
│  Scenario ID: ransomware_03287   Total Nodes: 10   Total Edges: 10           │
│  Typology Archetype: RANSOMWARE                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
                           [*] Graph Component Census                           
╭──────────────────────┬─────────────┬───────────────────────────┬─────────────╮
│ Node Type            │       Count │ Relationship / Edge Type  │       Count │
├──────────────────────┼─────────────┼───────────────────────────┼─────────────┤
│ Transaction          │           3 │ SENT                      │           4 │
│ Wallet               │           5 │ RECEIVED                  │           3 │
│ IP                   │           2 │ BROADCAST                 │           3 │
╰──────────────────────┴─────────────┴───────────────────────────┴─────────────╯

◈ Scenario Structure: ransomware_03287
├── TX 634499094 (2016-07-14 12:08:24) · Fee: 0.00006743 BTC
│   ├── BROADCAST by 171.87.50.149 agent: /Satoshi:0.20.1/
│   ├── ◀ INFLOWS (Senders)
│   │   └── 19YdsoctKAxpN8FJ837tNETi999x 53,042,178.1614 BTC
│   └── ▶ OUTFLOWS (Recipients)
│       └── 1jLgHKBTV4wPz8zugRhGrKfs6qcs 53,042,178.1614 BTC
├── TX 187888339 (2016-07-14 12:12:29) · Fee: 0.00002729 BTC
│   ├── BROADCAST by 29.161.96.242 agent: /Satoshi:22.0.0/
│   ├── ◀ INFLOWS (Senders)
│   │   ├── 1jLgHKBTV4wPz8zugRhGrKfs6qcs 53,042,178.1614 BTC
│   │   └── 1wiZNogq4CjrpskLjoAwZfiRpVwkf 4,562,351.1853 BTC
│   └── ▶ OUTFLOWS (Recipients)
│       └── 1wyjiCSKUZtym1hXSXRPnCgbHi6rhqU 57,604,529.3466 BTC
└── TX 667981831 (2016-07-14 12:51:46) · Fee: 0.00001619 BTC
    ├── BROADCAST by 171.87.50.149 agent: /Satoshi:21.1.0/
    ├── ◀ INFLOWS (Senders)
    │   └── 1wyjiCSKUZtym1hXSXRPnCgbHi6rhqU 57,604,529.3466 BTC
    └── ▶ OUTFLOWS (Recipients)
        └── 1CefSqVGhYCCkQuGppK3EqGxuQZD8VJE 57,604,529.3466 BTC
```

---

### `trace <src_address> <dst_address>`
Computes the directed multi-hop shortest path between two Bitcoin wallets across the transaction graph.

```bash
bitkaun@investigation:~$ trace 1jLgHKBTV4wPz8zugRhGrKfs6qcs 1wyjiCSKUZtym1hXSXRPnCgbHi6rhqU
```

**Example Output:**
```
╭────────────────── [*] MULTI-HOP FORENSIC TRANSACTION TRACE ──────────────────╮
│  Source:      1jLgHKBTV4wPz8zugRhGrKfs6qcs                                   │
│  Destination: 1wyjiCSKUZtym1hXSXRPnCgbHi6rhqU                                │
│  Trajectory:  PATH RESOLVED   Hop Distance: 1   Total Value: 57,604,529 BTC  │
╰──────────────────────────────────────────────────────────────────────────────╯
                     [*] Directed Transaction Flow Sequence                     
╭─────┬───────────────────┬───────────────────┬───────────┬──────────────┬────────────┬────────────╮
│ Hop │ From Wallet       │ To Wallet         │      TxID │       Amount │ Timestamp  │ Typology   │
├─────┼───────────────────┼───────────────────┼───────────┼──────────────┼────────────┼────────────┤
│ #1  │ 1jLgHKBTV4wPz8... │ 1wyjiCSKUZtym1... │ 187888339 │ 57,604,529 B │ 2016-07-14 │ RANSOMWARE │
╰─────┴───────────────────┴───────────────────┴───────────┴──────────────┴────────────┴────────────╯
```

---

### `alerts` & `alerts --detail <candidate_id>`
Displays the prioritized feed of forensic AML candidate alerts ranked by ML risk score and confidence.

```bash
# View top prioritized alerts
bitkaun@investigation:~$ alerts

# View top N alerts
bitkaun@investigation:~$ alerts --limit 10

# Deep-dive into SHAP feature attributions and telemetry provenance
bitkaun@investigation:~$ alerts --detail cand_ransom_ransomware_03287_187888339
```

**Deep Evidence Dossier Output:**
- Candidate & Scenario metadata
- Binary Risk & Multiclass Typology Confidence
- Heuristic corroboration confirmation
- Forensic plain-English rationale
- Top 10 XGBoost / TreeSHAP Feature Attributions with values, directional impacts (`▲ ELEVATES RISK` / `▼ LOWERS RISK`), and exact SHAP impact scores
- P2P Origin IPs, ASNs, Countries, and Infrastructure node distribution

---

### Utility Commands
- `help [command]` — Display command index or detailed syntax for a specific command
- `clear` — Clear the screen and refresh the BitKaun header banner
- `exit` / `quit` — Gracefully disconnect and exit the REPL session

---

## 5. Offline & Cross-Platform Compliance

- **Zero Cloud Network Calls:** Strictly binds and communicates with `localhost:8000`.
- **Pure Pathlib & Standard Encodings:** Uses `pathlib.Path` for path manipulations and enforces UTF-8 string encoding across all operating systems.
- **Cross-Platform Compatibility:** Runs on native Linux, WSL2, macOS, and Windows PowerShell/Terminal without platform-specific system calls.
