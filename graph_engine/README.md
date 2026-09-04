# Bitcoin AML Graph Engine

Comprehensive documentation, algorithms, architecture, benchmark metrics, and usage guides are available in:
- **[`GRAPH_ENGINE.md`](../GRAPH_ENGINE.md)** (Root Workspace Documentation)

## Quick Start

### Activate Environment & Run Pipeline
```powershell
.\graph_engine\.venv\Scripts\python -m graph_engine.main
```

### Run with Custom Paths
```powershell
.\graph_engine\.venv\Scripts\python -m graph_engine.main --data-dir data/processed --output-dir output
```

### Skip Ground-Truth Validation
```powershell
.\graph_engine\.venv\Scripts\python -m graph_engine.main --no-validate
```

## Module Structure

- [`config.py`](config.py): Centralized configuration parameters and detection thresholds.
- [`ingest.py`](ingest.py): Loads, parses, and validates blockchain and network CSVs.
- [`graph_build.py`](graph_build.py): Constructs heterogeneous graph and wallet-to-wallet projections.
- [`structures.py`](structures.py): Shared dataclass definitions (`CandidateStructure`).
- [`detectors/peeling_chain.py`](detectors/peeling_chain.py): Peeling chain detector.
- [`detectors/layering.py`](detectors/layering.py): Fan-out/fan-in layering detector.
- [`detectors/mixing.py`](detectors/mixing.py): CoinJoin mixing cluster detector (Louvain community detection).
- [`features.py`](features.py): Network layer feature enrichment.
- [`export.py`](export.py): Graph JSON & ML feature table exporter.
- [`validate.py`](validate.py): Ground-truth validation and evaluation metrics.
- [`main.py`](main.py): Pipeline orchestration CLI.
