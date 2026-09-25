# BitKaun? — Documentation Content Handbook

> **Frontend handoff:** This file contains the content for the documentation website. Each numbered section can become a documentation page. Page slugs below are suggested website routes, not routes already implemented in the application.
>
> **Reviewed:** 25 September 2026, branch `cli`, application source at commit `10ab219`.
> **Verification scope:** Source and configuration review. Setup commands, runtime behavior, and model performance were not executed or benchmarked for this handoff. “Implemented” means a corresponding code path exists; known gaps are documented below.

## Documentation navigation

| Group | Page | Suggested slug | Content |
| --- | --- | --- | --- |
| Getting started | Introduction | `/docs/introduction` | Section 1 |
| Getting started | Local setup | `/docs/setup` | Section 2 |
| Getting started | Your first investigation | `/docs/quickstart` | Section 3 |
| Reference | Web terminal commands | `/docs/commands` | Section 4 |
| Reference | Standalone CLI | `/docs/cli` | Section 5 |
| Investigation | Upload and correlate data | `/docs/ingestion` | Section 6 |
| Investigation | Graphs and transaction analysis | `/docs/graphs` | Section 7 |
| Investigation | ML scores and explanations | `/docs/ml` | Section 8 |
| Investigation | Cases and reports | `/docs/cases` | Section 9 |
| Developer guide | Architecture and project structure | `/docs/architecture` | Section 10 |
| Developer guide | Local API reference | `/docs/api` | Section 11 |
| Developer guide | Data and model versions | `/docs/data-models` | Section 12 |
| Help | Troubleshooting | `/docs/troubleshooting` | Section 13 |
| Help | FAQ and glossary | `/docs/faq` | Section 14 |
| Project status | Deadlock Protocol | `/docs/deadlock` | Section 15 |
| Maintainers | Content integration notes | Internal handoff | Section 16 |

---

## 1. Introduction

### Page title

Investigate Bitcoin transaction flows with explainable evidence.

### Short description

BitKaun? is a local Bitcoin forensic analysis platform that combines on-chain transaction records with recorded peer-to-peer network telemetry. Explore transaction graphs, inspect wallets, review suspicious structures, and organize investigation findings in one workspace.

### Project identity

- **Project:** BitKaun? AML Forensics / BitKaun? Forensic Terminal.
- **Problem statement:** SIH PS146 — AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic.
- **Intended users:** Investigators, financial intelligence analysts, developers, and hackathon evaluators.
- **Runtime model:** Local backend with a browser terminal and an optional Python CLI.
- **Data context:** Bundled datasets and demonstration presets include synthetic/generated data. Results describe the loaded records, not all activity on the Bitcoin network.

### What you can do

| Capability | Description |
| --- | --- |
| Dual-layer inspection | View transaction inputs, outputs, fees, and associated relay observations together. |
| Interactive graphs | Explore Wallet, Transaction, and IP nodes and their relationships. |
| Alert triage | Review ranked candidate alerts with binary risk, typology confidence, and supporting evidence. |
| Explainable ML | Inspect feature contributions for binary and typology predictions. |
| Anomaly analysis | Measure how unusual a scenario is relative to the model's normal reference distribution. |
| Upload and correlation | Import records and join ledger and network CSVs by transaction ID. |
| Case management | Create case folders and save supported investigation outputs. |
| Reporting | Generate investigative summaries and print-ready dossier views. |

### Scope

BitKaun supports analysis and triage. A suspicious score is a model assessment, a relay IP is an observed network node, and a wallet cluster is a heuristic relationship. None independently establishes a person's identity or criminal involvement. The application does not freeze Bitcoin funds.

### Suggested links

**Set up locally** → Section 2 · **Start an investigation** → Section 3 · **Browse commands** → Section 4.

---

## 2. Local setup

### Page title

Run your forensic workspace locally.

Use two terminals: one for FastAPI and one for Vite. Run commands from the repository root unless a step explicitly changes directories.

### 2.1 Prerequisites

| Requirement | Recommended project environment |
| --- | --- |
| Operating system | Ubuntu 24.04 LTS, native or through Windows WSL2 |
| Python | 3.11 or 3.12 |
| Node.js | 20.x or newer |
| npm | 10.x or newer |
| Git | Required to clone/update the repository |
| Browser | A current browser with WebGL enabled |
| Project artifacts | Master CSV pair, model manifest, matching model files, encoders, and anomaly normalization file |

Initial package installation requires internet access or pre-provisioned packages. Local investigation is designed to run with locally available data and models. A fresh machine needs dependencies installed before an offline demonstration.

There is no verified minimum RAM/GPU requirement in the current source. Data and indexes are loaded into memory; startup and graph rendering depend on dataset size and hardware.

### 2.2 Get the repository

For a new checkout of the reviewed branch:

```bash
git clone --branch cli https://github.com/umang24-cyber/SIH-2026.git
cd SIH-2026
```

For an existing checkout, open its root directory. Confirm it contains `package.json`, `backend/`, `data/`, and `ml/`.

### 2.3 Create a Python environment

**Ubuntu / WSL2:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If virtual-environment creation reports a missing `venv` or `ensurepip` package, install the appropriate venv package for the Python interpreter being used. For Ubuntu's default Python:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

**Windows PowerShell alternative**, with Python 3.11 installed:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` for the following Python commands. Activation is convenient, not required to use the environment.

### 2.4 Install backend dependencies

With the environment active:

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

**Important:** The root `requirements.txt` mainly covers broader graph-analysis tooling. It does not replace `backend/requirements.txt`, which includes FastAPI, Uvicorn, XGBoost, SHAP, and multipart upload support.

For development involving the additional graph tooling, also install:

```bash
python -m pip install -r requirements.txt
```

Dependency files specify minimum versions rather than a fully frozen Python environment. Model serialization compatibility should be checked against the environment used to produce the artifacts.

### 2.5 Confirm data and model artifacts

The server needs these artifact groups before it can finish startup:

| Artifact | Selection used by the source |
| --- | --- |
| Master ledger and network CSVs | `data/processed_v8/` if that directory exists; otherwise `data/processed/` |
| Model manifest | `ml/manifests/MANIFEST_v8.json` if present; otherwise `MANIFEST_v7_candidate.json` |
| Binary and typology models | Filenames declared in the selected manifest, under `ml/models/` |
| Script-type encoder | `data/processed_v8/script_type_encoder.json` if the file exists; otherwise `data/processed/script_type_encoder.json` |
| Typology labels | `ml/models/typology_label_encoder.json` |
| Anomaly model | `ml/models/anomaly_model_v8.pkl` if present; otherwise `anomaly_model_v7.pkl` |
| Anomaly normalization | `ml/models/anomaly_norm_params.json` |

The master filenames are `blockchain_transactions.csv` and `network_metadata.csv`.

The reviewed workspace has `data/processed/` and V9 data directories, but no `data/processed_v8/`. Its current configuration therefore selects `data/processed/` for master data while selecting the available V8 manifest/models. This describes path selection, not a verified data/model compatibility result. V9 files are not automatically selected. See Section 12 before changing datasets.

### 2.6 Start the backend — terminal 1

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal open. Startup initializes SQLite, loads the master dataset and persisted custom transactions, loads ML artifacts, and builds CIOH clusters. Wait for Uvicorn's application-startup completion message.

Open these local URLs in the browser:

- `http://127.0.0.1:8000/health` — current status and dataset counters.
- `http://127.0.0.1:8000/docs` — FastAPI Swagger interface.
- `http://127.0.0.1:8000/openapi.json` — machine-readable API schema.

The default FastAPI documentation interface may need its external JavaScript/CSS assets available. `/openapi.json` is served locally; do not treat Swagger's availability as proof of a fully offline docs UI.

### 2.7 Start the frontend — terminal 2

Open another terminal in the repository root:

```bash
npm ci
npm run dev
```

Open `http://localhost:5173`, or the exact URL printed by Vite if it chooses another available port. Use the landing page's **CLI TOOL** button to enter the browser terminal.

Vite forwards configured local API paths to `http://localhost:8000`. The browser API client uses relative URLs. No `.env` file or external API key is required by this default local configuration.

### 2.8 Verify the setup

Run these commands **inside the browser terminal**, one at a time:

```text
status
scenarios
help
```

Expected checks:

- `/health` reports `ONLINE` after initialization.
- `loaded_transactions` and scenario counts reflect the local dataset and persisted imports.
- `scenarios` returns indexed scenario IDs.
- `help` opens the command manual.

`alert_count` can be zero before the first alert scan. Startup deliberately defers detection until it is needed; this counter alone does not prove there are no suspicious candidates.

### 2.9 Build and validation commands

**Frontend type-check and build:**

```bash
npm run build
```

**Existing Python test suites**, from the root with the backend environment active:

```bash
python -m pytest backend/tests tests
```

These are project verification commands, not recorded passing results for this handoff. Some tests need data/models or additional dependencies; inspect a failing test's requirements rather than replacing missing artifacts with dummy files.

**Legacy dataset validation**, specifically for `data/processed/` and the v2 assumptions:

```bash
python data_pipeline/validate_v2.py
```

This validator does not automatically follow runtime data-directory selection. Its historical 15-check result must not be displayed as a fresh validation result for V8/V9 data.

### 2.10 Configuration, helper scripts, and shutdown

- API target/proxy: `vite.config.ts`.
- Backend settings and data paths: `backend/app/core/config.py`.
- Browser API client: `src/services/api.ts`.
- Backend-only helper: `bash run_backend.sh`.
- Combined Linux helper: `bash run_ubuntu.sh`, after installing dependencies and frontend packages.

The helper scripts contain machine-specific Conda detection, and the combined script only installs Python dependencies when it creates an environment. The explicit two-terminal steps above make startup easier to diagnose.

`Settings` currently extends Pydantic `BaseModel`, not environment-backed settings. Creating `PORT`, `DATABASE_URL`, or `VITE_API_URL` variables does not automatically configure this application.

Stop each running development server with **Ctrl+C** in its terminal.

**Build serving note:** Vite builds to root `dist/`. The current FastAPI static-path calculation points to `backend/dist/`. A successful frontend build alone does not establish single-server hosting. `npm run preview` is a frontend preview, not a verified backend deployment configuration.

---

## 3. Your first investigation

### Page title

From a scenario to an evidence-backed finding.

This walkthrough uses the browser terminal. In command syntax, `<...>` means an identifier copied from your actual results; brackets are not part of the entered command.

1. Run `status` to confirm the backend is online.
2. Run `scenarios` and copy an exact scenario ID. Prefix filters such as `scenarios peel 1` depend on the IDs in the loaded dataset.
3. Run `graph <scenario_id>` to open that scenario's topology.
4. Select a transaction or wallet, or run `inspect <txid>` / `inspect <address>`.
5. Run `flow <txid>` to inspect input/output allocation and fees.
6. Run `anomaly <scenario_id>` to inspect independent unusualness scoring.
7. Run `alerts --limit 10`. Allow the initial scan to complete.
8. Copy a returned candidate ID and run `alerts --detail <candidate_id>` to inspect evidence and SHAP contributions.
9. Run `init demo_review` to create and activate a local case.
10. Run `alerts --detail <candidate_id> --save` to save that evidence to the case.
11. Run `ls` to check saved artifacts.
12. Run `dossier <txid>` to generate an investigative summary for the selected transaction.

Copy IDs from the running application rather than from old screenshots. A scenario name describes a dataset grouping; it is not itself a verified model prediction.

**Next:** Learn command syntax in Section 4 or bring your own data using Section 6.

---

## 4. Web terminal command reference

Commands in this section are entered in the **browser's BitKaun terminal**, not in PowerShell/Bash. They are based on the dispatcher in `src/App.tsx`, which takes precedence over older help text.

### 4.1 Investigation commands

| Command syntax | Supported aliases | What it does |
| --- | --- | --- |
| `graph <scenario_id>` | `dashboard`, `g`, `nodes` | Opens or switches the 3D graph. Supplying an exact ID avoids dataset-specific defaults. |
| `inspect <txid-or-address>` | `i` | Inspects a dataset transaction or wallet. |
| `search <query>` | `find`, `query` | Searches transactions, wallets, scenarios, and recorded network information. |
| `scenarios [prefix] [page]` | `clusters` | Browses indexed scenarios, with optional prefix filtering and pagination. A numeric first argument selects a page. |
| `trace <source_address> <target_address>` | `route` | Searches for a directed path between two wallets. |
| `taint <seed_address>` | — | Estimates downstream exposure using proportional allocation and per-hop decay. |
| `flow <txid>` | `decompose` | Shows financial input/output structure and associated context. Uses numeric dataset IDs. |
| `communities <scenario_id>` | `community`, `syndicates` | Shows graph-community partitions. |
| `anomaly <scenario_id>` | `unusual` | Requests a scenario-level Isolation Forest score. |
| `alerts` | `alert` | Retrieves the ranked candidate queue. |
| `alerts --limit 10` | — | Requests up to 10 candidates; backend limit range is 1–200. |
| `alerts --pattern peeling_chain` | — | Filters by typology. Other values include `layering`, `mixing`, and `ransomware`. |
| `alerts --detail <candidate_id>` | — | Opens evidence for a candidate returned by the queue. |
| `dossier <txid-or-scenario_id>` | `dossiers`, `report` | Generates a summary. The backend also resolves recognized candidate IDs; a scenario/candidate resolves to a representative transaction. |
| `dossier list` | — | Lists saved system-generated dossiers. |
| `tor` / `tor <txid>` | — | Shows aggregate Tor-relay observations or a transaction-specific telemetry profile. |

The web command parser accepts confidence-related alert flags, but the current backend `/alerts` route does not declare `min_confidence`. Do not document those flags as functioning server-side filters.

### 4.2 Ingestion and monitoring

| Command | What it does |
| --- | --- |
| `correlate` | Opens the dual-CSV upload/correlation workspace. Aliases: `upload`, `dualstream`. |
| `ingest` | Displays ingestion usage. |
| `ingest sample ransomware` | Imports the built-in ransomware-labelled demonstration transaction. |
| `ingest sample peeling_chain` | Imports the built-in peeling demonstration transaction. |
| `ingest sample mixing` | Imports the built-in mixing demonstration transaction. |
| `ingest sample licit` | Imports the built-in licit demonstration transaction. |
| `ingest <raw_json>` | Imports a transaction JSON object. Use the canonical field names in Section 6. |
| `logs [count]` | Fetches a telemetry batch, default 15, constrained to 1–100. Aliases: `log`, `stream`. |
| `telemetry` | Shows aggregated recorded network statistics. Aliases: `stats`, `p2p`. |
| `benchmark` | Opens the current fixed demo scorecard. Aliases: `eval`, `metrics`, `accuracy`. See Section 8. |
| `status` | Shows backend status and active-case context. Aliases: `sys`, `health`. |

`logs` / `stream` performs a batch request, not a continuous live Bitcoin connection. `ingest` imports records into the local application; it does not broadcast a Bitcoin transaction. The web dispatcher does not implement `inject`, despite that alias appearing in older registry text.

### 4.3 Cases and utilities

| Command | What it does |
| --- | --- |
| `init <case_name>` | Creates and activates a case. Prefer a simple name such as `demo_review`. |
| `cases` | Lists available cases. |
| `cd <case_name>` | Activates an existing case. Aliases include `case`, `checkout`, and `use`. |
| `cd ..` | Clears the active-case selection. |
| `ls [case_name]` | Lists artifacts in the active or specified case. Alias: `list`. |
| `help [command]` | Opens the in-app manual. Aliases: `man`, `?`. Some registry descriptions lag the dispatcher. |
| `sound on` / `sound off` | Controls procedural audio. `sound` alone toggles it; alias: `audio`. |
| `clear` | Clears displayed terminal output. Alias: `cls`. |
| `reboot` | Replays the splash screen; it does not restart the backend. Aliases: `splash`, `boot`. |

Supported save examples: `alerts --save`, `alerts --detail <candidate_id> --save`, and `dossier <txid> --save`. Create or activate a case first. Do not imply that every command supports `--save`.

---

## 5. Standalone Python CLI

### Page title

Use BitKaun from your system terminal.

The Python CLI is another local backend client. It supports an interactive REPL and one-shot commands. The browser terminal and Python CLI have separate dispatchers; aliases and file-upload syntax are not identical.

### Installation

With the Python environment active, from the repository root:

```bash
python -m pip install -e ./cli
bitkaun status
```

The backend must already be running. The current CLI default target is `http://127.0.0.1:8000`, defined in `cli/bitkaun_cli/api_client.py`.

### Usage

```bash
bitkaun
```

Inside the REPL, enter `help`, `status`, or `scenarios`. Use `exit` or `quit` to leave.

One-shot usage:

```bash
bitkaun help
bitkaun status
bitkaun scenarios
bitkaun alerts --limit 10
```

Core commands include `inspect`, `graph`, `trace`, `alerts`, `taint`, `flow`, `communities`, `anomaly`, `search`, `scenarios`, `telemetry`, `dossier`, `tor`, `ingest`, `logs`, and case-management commands.

### Differences from the browser

- CLI graph output is terminal-oriented, not the browser's interactive WebGL canvas.
- CLI `correlate` accepts two local CSV file paths. With no paths it submits a built-in sample pair; browser `correlate` opens an upload workspace.
- Browser `sound` and `reboot` are UI commands, not Python CLI features.
- Do not use the Python CLI's one-shot exit code as a comprehensive automation success signal: the current entry point exits with code zero after dispatch, including some handled errors. Read its result/error output.

Further source: [CLI README](../cli/README.md), with current dispatch behavior in [main.py](../cli/bitkaun_cli/main.py).

---

## 6. Upload and correlate data

### Page title

Bring ledger and network observations into one investigation.

### 6.1 Browser workflow

1. Enter `correlate` in the browser terminal.
2. Select a ledger CSV and a network CSV, or use the workspace's sample-pair control.
3. Run correlation and wait for the result.
4. Review matched, unmatched, duplicate, and newly indexed counts.
5. Review the returned scenario analyses, including unavailable states and sample-size messages.
6. Open an exact returned scenario ID in the graph or inspect a returned transaction.

The browser `upload` command currently opens this same two-stream workspace. The separate backend file endpoint also accepts CSV, JSON, and XML; do not describe the two-CSV UI as an XML uploader.

### 6.2 Canonical input fields

These are the canonical fields to supply for meaningful analysis, not a claim that the permissive importer rejects every missing field.

**Ledger data**

| Field | Meaning / format |
| --- | --- |
| `txid` | Stable transaction identifier used to join both streams; numeric dataset IDs are the normal API representation. |
| `timestamp` | Transaction/block timestamp in a consistently parseable datetime format. |
| `input_addresses` | JSON array of input-address strings. |
| `output_addresses` | JSON array of output-address strings. |
| `input_amounts` | JSON array of BTC amounts aligned by index with input addresses. |
| `output_amounts` | JSON array of BTC amounts aligned by index with output addresses. |
| `fee_btc` | Transaction fee in BTC. |
| `script_type` | Script category such as `P2PKH`, `P2SH`, `P2WPKH`, or `P2WSH`. |
| `scenario_id` | Grouping key for related transactions and scenario-level scoring. |

**Network data**

| Field | Meaning / format |
| --- | --- |
| `txid` | Matching ledger identifier. |
| `relay_timestamp` | Time of the recorded relay observation. |
| `relay_ip` | Observed relay IP; not a proven transaction-originator identity. |
| `relay_port` | Numeric relay port. |
| `node_type` | Recorded infrastructure category, such as `residential`, `datacenter`, `tor_exit_node`, or `vpn_proxy`. |
| `country_code` | Recorded country code for the relay. |
| `asn` | Recorded autonomous-system identifier. |
| `isp` | Recorded provider label. |
| `user_agent` | Recorded client/software identifier. |
| `propagation_delta_ms` | Propagation timing value, when provided; otherwise the importer attempts derivation. |

Preserve the same `scenario_id` for related ledger records. Supply BTC amounts explicitly, escape JSON arrays correctly inside CSV cells, align address and amount arrays, and check `sum(inputs) ≈ sum(outputs) + fee` before import. A successful import response is not a complete accounting-integrity certificate.

The importer can generate/remap IDs and fill missing values. Supply explicit IDs and observations rather than relying on those fallbacks. Full Bitcoin hash support is not equivalent to the project's internal numeric-ID model.

`protocol_version` exists in master-data/response schemas but is not preserved by the current custom-record normalizer. Do not promise arbitrary extra-column round trips through uploads.

### 6.3 Formats and correlation behavior

- **JSON file:** One object or an array of transaction objects.
- **CSV file:** Column names plus records; array columns contain JSON arrays.
- **XML file:** A `transaction` element or a parent containing `transaction` elements, interpreted by the existing parser.
- **Dual CSV correlation:** Matches by `txid`, then retains ledger-only and network-only records as well. This is full-outer-style correlation, unlike the startup master loader's inner join.

Unmatched or incomplete rows may receive normalizer defaults. An imported record is not proof that both evidence layers were observed.

### 6.4 Result labels

| Result | Meaning |
| --- | --- |
| `input_records` | Parsed input count; in dual-stream mode this includes records from both files. |
| `unique_records` | Unique transaction IDs represented by the resulting batch. |
| `newly_indexed_records` | Records whose IDs were not previously indexed. |
| `duplicate_records` | Duplicate input IDs and/or IDs already indexed, according to the endpoint's counting logic. |
| `matched_records` | IDs present in both uploaded streams. |
| `ledger_only_records` / `network_only_records` | IDs present on only one side. |
| `correlation_rate` | Matched IDs divided by the larger unique-stream size; range 0–1. |
| `scenario_results` | Per-scenario scoring output and analysis messages. |

`analysis_status=UNAVAILABLE` means scoring was unavailable. Display that state and its message, not a zero-risk badge. Scenarios with fewer than three transactions can carry a sample-size warning; this is a disclosure, not an automatic scoring rejection.

---

## 7. Graphs and transaction analysis

### Page title

Follow relationships, not just individual transactions.

### Graph vocabulary

| Item | Meaning |
| --- | --- |
| Wallet node | An address observed in transaction inputs or outputs. |
| Transaction node | A transaction record connecting its input and output addresses. |
| IP node | A recorded relay associated with a transaction. |
| `SENT` edge | Wallet → Transaction, with an input amount. |
| `RECEIVED` edge | Transaction → Wallet, with an output amount. |
| `BROADCAST` edge | IP → Transaction, with recorded relay context. |

### Analysis tools

- **Inspect:** Review one transaction's fields or a wallet's activity within the loaded dataset. Wallet totals are dataset-scoped aggregates, not a live spendable-balance query.
- **Trace:** Find a directed path between wallets. A shortest-hop path does not necessarily mean the fastest path by elapsed time or the exact movement of individual satoshis.
- **Taint:** Estimate exposure from a seed with proportional splits and distance decay. The current service implements this proportional approach; a separately selectable FIFO mode is not exposed.
- **Communities:** Partition a graph using structural connectivity. A dense community is not proof of a criminal organization.
- **CIOH:** Link addresses appearing together as transaction inputs. Common-input ownership is a heuristic and can be misleading in collaborative transactions such as CoinJoin.

The wallet-profile service's `is_licit_exchange` flag is inferred from activity/volume thresholds. It is not a verified exchange-ownership record or a guarantee that the wallet's activity is legitimate.

### Typology descriptions

| Typology | Structural idea |
| --- | --- |
| Peeling chain | Repeated transfers where part of the value is paid out and a remainder continues through subsequent addresses. |
| Layering | Funds spread across intermediaries and may later reconverge. |
| Mixing / CoinJoin-like structure | Multi-party, often similarly denominated inputs/outputs that complicate attribution. |
| Ransomware-associated pattern | A model category learned from the project's scenario data, requiring supporting investigative context. |

Use exact scenario IDs from `scenarios`. The graph route has legacy aliases and fuzzy fallbacks, including a layering alias that can resolve to a normal scenario. The returned `scenario_id` is the actual graph identity; an alias is not a classification.

---

## 8. ML scores, explanations, and evaluation

### Page title

Understand what each score tells you.

| Output | Range | Interpretation |
| --- | --- | --- |
| `risk_score` | 0–1 | Binary XGBoost model estimate of `P(illicit)` for the analyzed scenario/context. |
| `binary_confidence` | 0–1 | The same binary probability, not an independent score to average with risk. |
| `typology_confidence` | 0–1 | Top-class probability from the separate typology classifier. |
| `anomaly_score` | 0–100 | Isolation Forest unusualness relative to its normal reference distribution; not a probability. |
| SHAP contribution | Signed value | Contribution of a feature toward or away from the explained model output. Not a standalone probability or causal proof. |

### Prediction scope

The selected manifest defines 46 features. Current serving uses scenario aggregates and graph features. A score shown while inspecting a transaction can use its complete indexed scenario; it should not automatically be labelled an independent per-transaction probability.

Feature groups include amounts/fees, input/output structure, timing, relay diversity, script types, and graph topology.

The ML manifest gate rejects `is_illicit`, `pattern_type`, `split`, `scenario_id`, and `is_licit_exchange` as model features. `scenario_id` is used for grouping/cache lookup, not as a numeric model input. This design rule is not a substitute for end-to-end leakage evaluation.

### Thresholds and unavailable states

- The binary decision threshold in `ml_service.py` is `0.50`.
- The candidate-scoring path uses `0.60` typology confidence to choose a confident label; lower-confidence output may be ambiguous.
- The basic `predict_risk` path decodes the top typology without the same ambiguity gate. Preserve the actual endpoint result and its context.
- Anomaly labels are `LOW` below 40, `MEDIUM` from 40 to below 70, and `HIGH` at 70 or above.
- Keep anomaly, binary risk, and typology confidence separate in copy and charts.
- Preserve unavailable/error messages. A missing model result does not mean a transaction is normal.

### Explainability

Evidence can include binary-model `ml_feature_attributions`, separate `typology_shap_attributions`, and a readable `typology_explanation`. Positive/negative contributions describe the particular output being explained. Show feature name, observed value, signed contribution, and model context together.

### Evaluation status

The current `/eval/benchmark` endpoint returns **hardcoded demonstration metrics**, including its F1 and latency values. It does not execute an evaluation or measure live inference latency when requested. Label the existing `benchmark` page accordingly; do not publish these numbers as verified runtime performance.

The repository also contains recorded research reports, including [Phase 5 frozen-test evaluation](PHASE5_FROZEN_TEST_EVALUATION.md) and [post-frozen size-failure analysis](PHASE5_POST_FROZEN_SIZE_FAILURE_ANALYSIS.md). These have their own V9 dataset/model scope, include failed size-only audit gates, and must not be presented as a fresh evaluation of the default V8 serving selection.

Any published metric needs its dataset version, model artifact, test split, evaluation date, and limitations. Reported synthetic-data performance is not established real-world generalization.

---

## 9. Cases and reports

### Page title

Keep investigation findings organized.

A case groups supported saved outputs into a local directory. It does not create an isolated dataset or model instance: the running backend still uses shared data/indexes.

### Basic case workflow

```text
init demo_review
cases
alerts --limit 10 --save
ls
cd ..
cd demo_review
```

Run these one at a time inside the browser terminal. The first command creates a case; the alert save writes an artifact rather than only displaying results.

### Storage locations

| Platform | Default application data location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\BitKaun` |
| Native Linux | `~/.local/share/BitKaun` |
| WSL2 | Reuses a discovered Windows `AppData/Local/BitKaun` directory when available; otherwise the Linux home-based directory. |

Under the selected directory:

- `bitkaun_forensics.db` — SQLite persistence for custom records, dossiers, and audit information.
- `reports/` — generated report files.
- `cases/` — case folders and active-case marker.
- Case folders contain `.bitkaun/case.json`, `reports/`, `dossiers/`, and `evidence/` as managed by the case API.

Use paths reported by startup and case responses when locating data. WSL discovery does not guarantee the same folder on every machine, especially when multiple Windows users have BitKaun directories.

### Reporting formats

- `/api/dossier/{txid}` generates structured JSON.
- `/api/dossier/{txid}/html` generates print-ready HTML; use browser printing to save it as PDF.
- `/alerts/{candidate_id}/export` returns a text/Markdown-style investigation summary.
- `dossier list` lists stored dossiers.

These are system-generated investigative summaries. They are not automatically issued freeze orders or certified court documents. Report generation is local and does not dispatch a notice to an exchange or agency.

Custom imports can survive restarts through SQLite. Persistence failures are logged, and enrichment of already-indexed records is not guaranteed to follow the same persistence path as new records. Keep original input files when repeatability matters.

---

## 10. Architecture and project structure

### Page title

How the local analysis pipeline fits together.

```text
Master ledger CSV + recorded network CSV
                 |
          Inner join on txid
                 |
     Parsing + in-memory data/indexes <---- Custom ingestion / dual-CSV correlation
                 |                                  |
        +--------+---------+                   SQLite persistence
        |                  |
 Graph / CIOH / tracing   Scenario features
        |                  |
 Structural evidence    XGBoost + Isolation Forest + SHAP
        |                  |
        +--------+---------+
                 |
          FastAPI local API
                 |
        +--------+---------+
        |                  |
 React browser terminal  Python CLI
        |
 Three.js graphs / evidence views / local case artifacts
```

The diagram describes responsibilities, not a guarantee that every endpoint invokes every engine. For example, replay does not currently return the full anomaly/SHAP bundle.

### Current implementation stack

| Area | Used in the reviewed implementation |
| --- | --- |
| Browser application | React 18, TypeScript, Vite 5 |
| 3D rendering | Three.js and canvas-generated textures |
| Backend | FastAPI, Uvicorn, Pydantic |
| Data processing | Pandas, NumPy |
| Graph analysis | NetworkX and project graph services |
| Served classifiers | XGBoost binary and typology models selected by manifest |
| Anomaly model | Serialized Isolation Forest |
| Explainability | SHAP / tree-model attribution paths |
| Persistence | SQLite plus local case/report files |
| Python CLI | Python console package with Rich and local HTTP client |
| Audio | Browser Web Audio API |

LightGBM and additional graph packages exist in dependency lists. That does not mean they are the selected serving model or that Neo4j/PostgreSQL are required to start the default application. The frontend package currently uses Three.js, not a required Cytoscape dependency.

### Source map

| Path | Responsibility |
| --- | --- |
| `src/App.tsx` | Browser state and command dispatch. |
| `src/components/LandingPage.tsx` | Landing page and entry to the terminal. |
| `src/components/views/` | Investigation views and upload workspace. |
| `src/graph/` | Graph components and supporting logic. |
| `src/services/api.ts` | Browser-facing local API client and types. |
| `src/audio/soundEngine.ts` | Procedural UI audio. |
| `backend/app/main.py` | FastAPI startup and registered routers. |
| `backend/app/api/` | Actual HTTP routes. |
| `backend/app/models/schemas.py` | Response/request schemas. |
| `backend/app/ingestion/` | Master loader, normalization, and file parsers. |
| `backend/app/services/` | Data, graph, ML, anomaly, clustering, case-adjacent reporting, and replay services. |
| `backend/app/db/` | SQLite connections and schema. |
| `cli/bitkaun_cli/` | Standalone CLI dispatch, rendering, commands, and case context. |
| `data/` | Bundled datasets, splits, and feature/encoder artifacts. |
| `data_pipeline/` | Dataset generators and validators. |
| `ml/` | Feature extraction, training/evaluation code, models, manifests, and reports. |
| `graph_engine/` | Additional graph-analysis tooling. |
| `backend/tests/`, `tests/` | Existing Python test suites. |

---

## 11. Local API reference

### Page title

Explore the backend contract.

Default development base URL: `http://127.0.0.1:8000`.

The table lists routes implemented in the reviewed router files. It is a navigation reference; exact request/response schemas are defined by those files and the running `/openapi.json`. Endpoint paths have mixed prefixes: do not automatically add `/api` to every route.

### 11.1 Health, lookup, and graphs

| Method | Path | Inputs / purpose |
| --- | --- | --- |
| GET | `/health` | Runtime health, counts, and uptime. Alias: `/api/health`. |
| GET | `/scenarios` | Optional `prefix`; `page` defaults to 1; `page_size` defaults to 20, maximum 100. |
| GET | `/scenarios/{scenario_id}` | Scenario profile. |
| GET | `/search` | Query `q` or its alias `query`; `limit` defaults to 20, range 1–100. |
| GET | `/entity/{address}` | Dataset-scoped wallet profile. |
| GET | `/entity/{address}/cluster` | CIOH-linked address cluster. |
| GET | `/transaction/{txid}` | Transaction and associated network observation. |
| GET | `/transaction/{txid}/flow` | Input/output flow context. |
| GET | `/graph/{scenario_id}` | Nodes and edges for the resolved scenario. |
| GET | `/graph/{scenario_id}/communities` | Structural community partitions. |
| GET | `/trace` | Required `src`, `dst`; `max_depth` defaults to 6, range 1–10. |
| GET | `/taint` | Required `seed_address`; `decay_rate` defaults to 0.85 (0.1–1); `max_depth` 5 (1–8); `min_taint` 0.01 (0.0001–0.5). |

### 11.2 Scores, evidence, and reporting

| Method | Path | Inputs / purpose |
| --- | --- | --- |
| GET | `/alerts` | `sort_by` defaults to `risk_score`; optional `pattern_type`; `limit` defaults to 50, range 1–200. |
| GET | `/alerts/{candidate_id}/evidence` | Candidate detail and model/structural evidence. |
| GET | `/alerts/{candidate_id}/export` | Text-based investigation-summary export. |
| GET | `/anomaly/{scenario_id}` | Independent scenario unusualness score. |
| GET | `/stats/telemetry` | Current recorded-network aggregate statistics. |
| GET | `/eval/benchmark` | Fixed demonstration scorecard, not a live evaluation. |
| GET | `/api/intel/tor-summary` | Aggregate Tor-relay observations. |
| GET | `/api/intel/tor-profiler/{txid}` | Transaction telemetry profile. |
| POST | `/api/intel/tor-profiler` | Body-based profile lookup; see its OpenAPI request schema. |
| GET | `/api/dossier/saved/list` | Stored investigative summaries. |
| GET | `/api/dossier/{txid}` | Generate structured dossier. Also resolves supported scenario/candidate identifiers. |
| GET | `/api/dossier/{txid}/html` | Print-ready dossier HTML. |

`total_alerts` is the count returned by the current `/alerts` handler after its filtering/limit; do not assume it is a separate total across every candidate in storage.

### 11.3 Ingestion and replay

| Method | Path | Inputs / purpose |
| --- | --- | --- |
| POST | `/api/ingest/transaction` | Transaction dictionary as a JSON body, normalized by the importer. |
| POST | `/api/ingest/file` | Multipart field `file`; CSV, JSON, or XML. |
| POST | `/api/ingest/correlate` | Multipart fields `ledger_file` and `network_file`; both parsed as CSV. |
| GET | `/api/ingest/scenario/{scenario_id}/analysis` | Cached or on-demand uploaded-scenario analysis. |
| GET | `/api/ingest/sample` | Optional `typology`; retrieves a demonstration preset. |
| GET | `/api/ingest/sample-pair` | Demonstration ledger/network CSV pair. |
| GET | `/api/stream/batch` | `limit` 20 (1–100), `offset` 0 or higher, `tor_only` false by default. |
| GET | `/api/stream/replay` | SSE response; `speed` 15 (1–100), `limit` 100 (1–1000), optional `scenario_id`. |
| POST | `/api/stream/reconcile` | `mempool_stream` and `block_stream` arrays; `max_window_seconds` defaults to 120. |

Replay emits `data:` frames containing JSON. It replays locally indexed records, not a Bitcoin network subscription. Unknown scenario filters currently fall back to the unfiltered indexed pool; this is not strict “scenario not found” behavior. A browser docs example should describe this explicitly.

The reconcile endpoint accepts complete arrays and matches records by transaction ID within a timestamp window. It is not an always-running incremental network collector.

### 11.4 Case management

| Method | Path | Inputs / purpose |
| --- | --- | --- |
| GET | `/cases` | List local cases. |
| GET | `/cases/active` | Active case details. |
| POST | `/cases/active` | JSON field `case_name`; an empty name clears selection. |
| DELETE | `/cases/active` | Clear selection, not delete the case directory. |
| POST | `/cases/init` | JSON field `case_name`; create/activate a case. |
| GET | `/cases/{case_name}/ls` | List artifacts; `active` refers to the active case. |
| POST | `/cases/{case_name}/save` | Fields `command_name`, `identifier`, `data`; optional `subfolder`, default `reports`. |

### 11.5 Errors and client-contract notes

- `400`: malformed/unusable upload or another route-specific input failure.
- `404`: the requested entity, scenario, candidate, or file target is unavailable where strict lookup applies.
- `422`: FastAPI parameter/schema validation failure.
- `429`: graph-request rate limit. The graph route currently allows up to 12 requests per 3 seconds using a shared limiter.
- `5xx` or startup failure: inspect the backend terminal for model, data, dependency, or processing errors.

Response details are route-dependent; do not replace every error with “no results.”

Known client drift:

- `src/services/api.ts` declares a `/stats/overview` call, but no matching route is registered in the reviewed backend.
- Its anomaly interface uses legacy names. The actual response uses `anomaly_score`, `anomaly_label`, `anomaly_raw_if_score`, `anomaly_high_threshold`, and `anomaly_interpretation`.
- The browser sends `min_confidence` to `/alerts`; that query field is not implemented by the current route.
- Some client defaults differ from direct API defaults, including trace and taint depths.

Use the backend response schema when preparing documentation examples rather than copying stale TypeScript types unchanged.

---

## 12. Data and model versions

### Page title

Know which artifacts your session is using.

Application version, dataset version, model version, and evaluation version are separate facts. The UI/API advertises `8.0.0`, but this label is not a dataset counter or an artifact-integrity check.

### Current selection rules

- Data directory selection uses the existence of `data/processed_v8/`, falling back to `data/processed/`.
- Model selection uses the V8 manifest if present, independently of which data directory was selected.
- V9 data/model artifacts exist in the reviewed workspace but are not selected by these default serving paths.
- The selected V8 manifest declares 46 features and references `binary_model_v8.ubj` and `typology_model_v8.ubj`.
- Some log/response labels still say V7. Inspect the selected paths and manifest when identifying artifacts.
- The configured expected row count is 294,639. Older documentation cites 82,078. Neither should be hardcoded as the current session's count.
- Persisted custom imports can change runtime counts relative to the master CSVs.

Use `/health` and `/stats/telemetry` for session counters. The master loader logs its selected file paths and warns, rather than automatically aborting, when its row count differs from the configured expectation.

### Dataset validation and research references

- [Data dictionary](../DATA_DICTIONARY.md): historical field definitions and dataset invariants; check its version before using numeric claims.
- [Dataset handoff](../data/DATASET_HANDOFF.md): data-team context.
- [V9 architecture](V9_FINAL_ARCHITECTURE.md): research/training architecture documentation.
- [Phase 5 evaluation](PHASE5_FROZEN_TEST_EVALUATION.md): recorded V9 results and failure disclosures.
- `data_pipeline/validate_v2.py`: fixed to `data/processed/` and v2 checks.
- `data_pipeline/validate_v8.py`: fixed to `data/processed_v8/`; writes a quality report and is not a selector for other dataset versions.

Do not rename directories or overwrite models solely to make the newest version label appear. Dataset, feature extraction, label encoder, normalization, and selected models need to be compatible as a set.

---

## 13. Troubleshooting

| Symptom | Check / next step |
| --- | --- |
| `No module named uvicorn`, `fastapi`, `xgboost`, or multipart-related startup error | Confirm the active Python environment and install `backend/requirements.txt`. Root requirements alone are insufficient. |
| `No module named backend` | Start Uvicorn from the repository root with `backend.app.main:app`. |
| Missing blockchain/network CSV | Read the path printed in the error. Check both required files in the selected data directory; an incomplete `processed_v8/` directory still takes priority. |
| Missing model/encoder or feature-count mismatch | Restore a compatible manifest, model pair, encoders, and anomaly artifacts. Do not use empty placeholder files. |
| Backend takes time to start | Wait for initialization logs; it loads data, builds indexes/clusters, and loads models. Check the actual error before repeatedly restarting. |
| UI opens but `status` fails | Confirm backend port 8000 and frontend proxy target. Vite serving the page does not imply FastAPI is running. |
| Vite opens a different port | Use its printed Local URL, or free the configured port. The configured default is 5173. |
| `npm ci` reports lockfile mismatch | Check whether `package.json` and `package-lock.json` belong to the same checkout. Resolve the dependency change intentionally. |
| No alerts immediately after startup | Alert detection is lazy. Request `alerts` and allow the first scan to finish. |
| A copied example scenario fails or resolves unexpectedly | Use an exact ID from the current `scenarios` result; legacy defaults and graph aliases are dataset-dependent. |
| `--confidence` does not change alert results | The backend route does not currently support the `min_confidence` filter sent by the browser. |
| Upload succeeds but scoring is unavailable | Read `analysis_status`, `analysis_message`, and `anomaly_message`; ingestion and model analysis are separate outcomes. |
| Unexpected imported amounts/telemetry | Inspect original inputs and normalization behavior. Missing fields may be default-filled; unmatched rows are retained by dual-stream correlation. |
| Low sample size warning | The uploaded scenario has fewer than three transactions; review scope and warning rather than treating the score as fully validated. |
| Blank or unstable 3D view | Check WebGL/hardware acceleration, use one graph view, try a smaller scenario, and inspect browser errors. |
| Rate-limit message | Slow repeated commands/graph requests. The browser also limits command bursts. |
| No active case when saving | Run `init demo_review` or `cd <existing_case>`; check `cases` and `status`. |
| Saved files are not in the repository | Check the application-data location and paths returned by the case API. |
| `bitkaun` is not recognized | Activate the environment where `python -m pip install -e ./cli` ran. |
| Built UI is not served by FastAPI | Review the root `dist/` versus `backend/dist/` static-path mismatch in Section 2. |
| `deadlock` or `inject` is unknown in the browser | These are not implemented web-dispatcher commands in this revision; use the documented commands. |

---

## 14. FAQ and glossary

### Does BitKaun need a Bitcoin node or wallet key?

The current local dataset workflow does not require a Bitcoin node, wallet private key, exchange account, or paid API credential.

### Is the displayed stream the real Bitcoin mempool?

No. Current replay/batch routes use locally indexed records. “Live” refers to local processing or timed replay, not an external network feed.

### Can I use it offline?

The investigation pipeline is designed for local data/models. Install dependencies and provision all assets beforehand. Test the exact demo path offline, including documentation assets; development package installation is not offline by default.

### Does 90% risk mean the wallet owner is 90% likely to be a criminal?

No. It is a model output for the analyzed data context. It is not an identity determination or a general-purpose probability of criminal guilt.

### Is an anomaly score of 90 the same as 90% risk?

No. Anomaly is a separate 0–100 unusualness score, not a probability.

### Does a Tor relay reveal the sender's real IP?

No. Recorded relay telemetry does not establish the true originator's IP or physical location. The profiler provides telemetry analysis, not demonstrated Tor deanonymization.

### Do I need Neo4j or PostgreSQL running?

Not for the reviewed default backend. It uses in-memory analysis and SQLite persistence.

### Can I switch to V9 just by adding its model files?

No. Current default selection is explicitly V8/V7-based. Adding V9 artifacts does not wire them into serving or establish compatibility.

### Are the landing page's DOCS and ANALYTICS cards working modules?

In the reviewed revision, they are placeholders. The CLI entry works as the terminal entry point; analytics-related terminal commands exist separately. This handbook supplies content for implementing the DOCS experience.

### Glossary

| Term | Meaning |
| --- | --- |
| AML | Anti-money laundering. |
| UTXO | Unspent transaction output; an output that can be spent as an input to a later transaction. |
| Scenario | A group of related records used by the project for analysis and evaluation. |
| Candidate | A structure or group flagged for further review. |
| Typology | A category of transaction behavior, such as layering or peeling. |
| P2P telemetry | Recorded observations from the peer-to-peer relay layer. |
| ASN | Autonomous System Number identifying a network operator's routing domain. |
| CIOH | Common-Input Ownership Heuristic. |
| SHAP | Feature-attribution method explaining contributions to model output. |
| SSE | Server-Sent Events, a one-way HTTP event stream. |
| Dossier | A generated investigation summary with supporting context. |
| Air-gapped operation | Running with necessary local resources without relying on external network access. |

---

## 15. Deadlock Protocol — planned demonstration mode

### Page title

Deadlock Protocol: an interactive forensic replay concept.

**Status: Planned / not available as a complete mode in the reviewed revision.**

The [Deadlock specification](../DEADLOCK_PROTOCOL.md) proposes a cinematic entry transition followed by a timed transaction replay, growing graph, critical-node visual changes, evidence display, and end-of-session summary.

### Existing building blocks

- Local SSE replay and telemetry batches.
- XGBoost scoring, separate anomaly service, and explainability functions.
- Three.js graph rendering and Bitcoin medallion textures.
- Procedural audio, including Pac-Man-style effects.
- CIOH clustering and investigative dossier generation.

### Missing integration

- Deadlock command, dedicated simulation view, and curtain/skull transition.
- Continuous browser replay connection for that mode.
- Unified replay payload containing wallet edges, anomaly, SHAP, and required evidence.
- Dedicated evaluate/scenario endpoints described by the specification.
- Critical-node mutation, session timer, final scorecard, and judge injection controls.

### Important implementation distinctions

- Current replay risk can use the complete indexed scenario, including transactions not yet emitted. It does not demonstrate past-only incremental threat detection.
- Replay's current critical flag is based on risk ≥ 0.75, Tor status, or typology flags. It does not implement the specification's risk/anomaly/chain-length conjunction.
- Specified latency targets and zero-false-positive examples are goals/examples, not verified runtime results.
- A future containment action should mean flagging/evidence preparation unless an actual authorized external process is separately implemented. No Bitcoin freeze mechanism is present.

**Suggested delivery order:** working replay and controls → past-only scoring and evidence → visual/audio presentation → optional sandbox injection. Keep this page marked planned until those pieces are implemented and verified.

---

## 16. Frontend content integration notes

This section is for the documentation implementer rather than the public article body.

### Content behavior

- Use the navigation table to split the handbook into pages, or render sections in one searchable document.
- Keep shell commands, browser-terminal commands, and API route signatures visually distinct. The language labels on code blocks indicate context.
- Keep identifiers in syntax examples non-clickable until a real result supplies their values. Do not make a copy button execute a literal `<scenario_id>`.
- Use local links between documentation pages. Repository source links below are provenance references, not already-mounted website routes.
- Display the review date/revision for status-sensitive sections.
- Preserve qualifiers on scenario-level scores, recorded relay information, fixed benchmark numbers, and planned functionality.
- Show loading, unavailable, empty-result, and error states separately if the docs include interactive demonstrations.

### Suggested reusable copy

| Context | Copy |
| --- | --- |
| Docs entry | “Learn the setup, commands, and investigation workflow.” |
| Setup intro | “Start the backend, launch the browser terminal, and verify your local workspace.” |
| Investigation CTA | “Start your first investigation” |
| Command search | “Search commands, setup steps, and concepts…” |
| API link | “View the local API schema” |
| Unknown score | “Analysis unavailable. Review the processing message.” |
| Scenario score label | “Scenario-level model risk” |
| Anomaly label | “Anomaly / unusualness score” |
| Relay label | “Observed relay IP” |
| Report action | “Generate investigation summary” |
| Deadlock status | “Planned — dedicated simulation mode is not implemented yet.” |
| Benchmark label | “Demonstration scorecard — fixed values, not a live evaluation.” |

### Source-of-truth references

| Topic | Verified source |
| --- | --- |
| Startup and router registration | [main.py](../backend/app/main.py) |
| Backend configuration and storage paths | [config.py](../backend/app/core/config.py), [database.py](../backend/app/db/database.py) |
| Dependency commands and frontend build | [backend requirements](../backend/requirements.txt), [root requirements](../requirements.txt), [package.json](../package.json), [Vite config](../vite.config.ts) |
| Web commands and aliases | [App.tsx](../src/App.tsx) |
| Browser API/type drift | [api.ts](../src/services/api.ts) |
| CLI commands and target | [CLI main](../cli/bitkaun_cli/main.py), [CLI client](../cli/bitkaun_cli/api_client.py) |
| Import formats and defaults | [parser.py](../backend/app/ingestion/parser.py), [ingest routes](../backend/app/api/routes_ingest.py) |
| Master loading and persistence | [loader.py](../backend/app/ingestion/loader.py), [data service](../backend/app/services/data_service.py) |
| Scores and artifact selection | [ML service](../backend/app/services/ml_service.py), [anomaly service](../backend/app/services/anomaly_service.py), [V8 manifest](../ml/manifests/MANIFEST_v8.json) |
| Response fields | [schemas.py](../backend/app/models/schemas.py) |
| Alert parameters | [alert routes](../backend/app/api/routes_alerts.py) |
| Benchmark limitations | [stats routes](../backend/app/api/routes_stats.py) |
| Cases and dossiers | [case routes](../backend/app/api/routes_cases.py), [dossier routes](../backend/app/api/routes_dossier.py) |
| Replay behavior | [stream routes](../backend/app/api/routes_stream.py), [streaming correlator](../backend/app/services/streaming_correlator.py) |
| Graph aliases and taint semantics | [graph routes](../backend/app/api/routes_graph.py), [taint service](../backend/app/services/taint_service.py) |
| Planned demonstration | [Deadlock specification](../DEADLOCK_PROTOCOL.md) |

When an older document disagrees with a current route, dispatcher, or configuration file, update the website against the implementation and retain the limitation until the implementation changes.
