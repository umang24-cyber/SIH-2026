# Backend Architecture & Data Ingestion Specification

> **Owner:** P6 (Team Lead & Backend Engineer)  
> **Source of Truth Reference:** [DATA_DICTIONARY.md](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md) · [API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md)

---

## 1. Data Ingestion & Storage Pipeline

The backend is responsible for reading the dual-layer processed CSV datasets from `data/processed/`, joining records on `txid`, validating accounting identities, and loading them into an accessible query layer.

### 1.1 Ingestion Workflow

```text
  data/processed/blockchain_transactions.csv
                     +
  data/processed/network_metadata.csv
                     |
                     v
  [Pandas Ingestion Engine]
  - 1:1 Inner Join on txid (Primary Key)
  - Deserialize JSON arrays:
      * input_addresses  -> List[str]
      * output_addresses -> List[str]
      * input_amounts    -> List[float]
      * output_amounts   -> List[float]
  - Parse UTC timestamps:
      * timestamp (block time)
      * relay_timestamp (P2P broadcast time)
  - Compute propagation_delta_ms = (timestamp - relay_timestamp)
                     |
                     v
  [Database Storage Layer]
  (Indexed on: txid, scenario_id, relay_ip)
```

### 1.2 Parsing JSON Array Columns in Python

Per Section 2a of `DATA_DICTIONARY.md`, transaction input/output addresses and amounts are stored as JSON-serialized strings. Ingestion code must parse these using `json.loads`:

```python
import json
import pandas as pd

def load_and_merge_datasets(blockchain_csv_path: str, network_csv_path: str) -> pd.DataFrame:
    df_chain = pd.read_csv(blockchain_csv_path)
    df_net = pd.read_csv(network_csv_path)

    # 1:1 join on txid
    df = pd.merge(df_chain, df_net, on="txid", suffixes=("", "_net"))
    
    # Reconcile duplicate scenario_id / split columns if present
    if "scenario_id_net" in df.columns:
        df.drop(columns=["scenario_id_net", "split_net"], inplace=True)

    # Parse JSON array columns
    array_cols = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]
    for col in array_cols:
        df[col] = df[col].apply(json.loads)

    # Convert timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["relay_timestamp"] = pd.to_datetime(df["relay_timestamp"], utc=True)
    df["propagation_delta_ms"] = (df["timestamp"] - df["relay_timestamp"]).dt.total_seconds() * 1000.0

    return df
```

---

## 2. Database Selection (Architecture Decision)

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| **SQLite (In-File / In-Memory)** | Zero external service setup; perfectly portable for offline WSL2/Linux air-gapped demo; trivial schema setup. | Concurrency limitations on simultaneous writes (not an issue for read-heavy forensic demo). | **[TODO: P6 Decision]** Recommended for Hackathon Prototype. |
| **PostgreSQL** | Native JSONB indexing; advanced indexing for address arrays; high concurrency. | Requires PostgreSQL service running in WSL2; extra deployment overhead in air-gapped setup. | Candidate for production phase. |

---

## 3. FastAPI Service Layer

The REST API is implemented with FastAPI (`app/main.py`) exposing the endpoints declared in `API_CONTRACT.md`:

```text
app/
├── main.py                     # FastAPI application factory & CORS configuration
├── api/
│   ├── routes_entity.py        # GET /entity/{address}
│   ├── routes_transaction.py   # GET /transaction/{txid}
│   ├── routes_graph.py         # GET /graph/{scenario_id}
│   └── routes_alerts.py        # GET /alerts & GET /alerts/{id}/evidence
├── core/
│   ├── config.py               # Application settings and data paths
│   └── database.py             # SQLite / DB connection session
├── models/
│   ├── schemas.py              # Pydantic response models (mirroring API_CONTRACT.md)
│   └── orm_models.py           # Database table definitions
└── services/
    ├── graph_service.py        # Interfacing P4 graph builder
    └── alert_service.py        # Interfacing P5 ML scoring & explanation engine
```

---

## 4. Open Backend TODOs & Decisions

- `[ ]` **[TODO: P6]** Finalize DB decision (SQLite vs Postgres) and implement schema migration script.
- `[ ]` **[TODO: P6]** Build caching layer for graph subgraphs (`/graph/{scenario_id}`) to ensure sub-50ms visualizer load times.
- `[ ]` **[TODO: P6]** Add unit tests for API endpoints validating response structures against `API_CONTRACT.md`.

---

## 5. Architectural Clarifications & Verification Audit Notes

### 5.1 Ingestion-Integration Confidence Discrepancy Note
- **Observed Phenomenon:** An earlier pre-freeze ingestion test report displayed identical numerical values for `binary_confidence` and `typology_confidence` across two test scenarios.
- **Root-Cause Analysis:** Re-execution against live frozen V7 models (`binary_model_v6.xgb` and `typology_model_v6.xgb`) confirms that `binary_confidence` ($P(\text{illicit})$ from the binary classifier) and `typology_confidence` (softmax probability from the multi-class typology model) are computed via completely separate inference routines (`ml_service.predict_single_scenario`). The original report's identical numbers resulted from an evaluation script transcription copy-paste artifact during manual markdown synthesis; current production code enforces distinct extraction channels with zero cross-field aliasing.

