# BitKaun Observatory — frontend handoff

The landing page's **Analytics / The Observatory** link should open a read-only model-and-data showcase, not an investigator case dashboard. The backend is already implemented under `/api/observatory`. No authentication, upload, inference call or external network request is needed from this page. Use the existing landing page design system; the frontend owner adds the page, route, navigation, charts, and flow diagrams.

## Start here

From the repository root, run the normal backend (`run_backend.bat` on Windows, or the existing Linux runner) and `npm run dev` in another terminal. Vite already proxies `/api` to port 8000. The backend also serves `GET /openapi.json` and Swagger at `/docs`; the Observatory contracts are Pydantic response models. Fetch using a relative path, e.g. `fetch('/api/observatory/performance')`.

To link the page, replace the `Coming soon` entry in `src/components/LandingPage.tsx` with a link to `/analytics`. `src/main.tsx` mounts one `App` inside `BrowserRouter`; **route rendering is conditional in `src/App.tsx`**, not a `<Routes>` table. Add an analytics page branch for `location.pathname === '/analytics'` there, and exclude that path from the current catch-all `DocsPage` condition. Also update `backend/app/main.py` frontend fallback to include `/analytics` so a direct refresh works on the production FastAPI static server. The landing page's current analytics item is a non-link teaser. Backend endpoint registration is already complete in `backend/app/main.py`; no frontend code was modified by this backend task.

### Origin, version, and truthfulness

- **Active runtime model: V8** (`backend/app/services/ml_service.py` selects `ml/manifests/MANIFEST_v8.json` when present). The overview and performance endpoints read **V8 saved evaluation reports** and check them against this active manifest. Numbers are not hand-entered into API code. Gain bars inspect the active V8 XGBoost model artifact. The dataset comes from `backend/app/core/config.py`'s active bundled `DATA_PROCESSED_DIR` (here `data/processed`, since `data/processed_v8` is absent).
- The repository also has newer V9 artifacts. Do **not** mix V9 frozen numbers into a V8 page or label the benchmark as a live inference metric. An optional V9 frozen-report path exists for deployments deliberately switching runtime manifest; V8 is what this checkout currently serves.
- The dataset is synthetic; benchmark metrics measure held-out synthetic scenarios, not real-world performance. On this checkout, the dataset response currently returns **294,693** transactions, **5,440** scenarios and **984,076** unique wallets; these are generated from local data at request time, not constants. Always render server values.
- V8 saved reports do **not** contain binary/typology confusion matrices, per-class precision/recall or ROC/PR curve coordinates. `confusion_matrix: null`, `per_class: []`, `curves_available: false`. Hide those charts or show the unavailable explanation; **do not synthesize a heatmap, loss/accuracy timeline, SHAP chart, or class bars from scalar metrics**.
- The older `/eval/benchmark` endpoint has unrelated hard-coded metrics; **use `/api/observatory/*`**.

## API quick reference

Every response is a `200` envelope with `schema_version: "1.0"`, `status: "available" | "unavailable"`, `meta`, `data`, and `message`. For unavailable artifacts: `data: null` and a non-empty `message`. Bad query params produce `422`. Treat an unavailable section independently, rather than blanking the entire page. Source timestamps and timeseries points are ISO UTC. Ratios are numbers in `[0, 1]`; display with `Intl.NumberFormat` and percent styling where appropriate. Counts remain integer counts.

| Endpoint | Params | Source and scope | Chart/UI |
| --- | --- | --- | --- |
| `GET /api/observatory/overview` | — | Active ML manifest + saved reports + bundled data | Headline metrics and model/version badges |
| `GET /api/observatory/dataset` | `bucket=day\|week\|month` (default month) | Aggregated bundled train + test ledger/network CSVs | Timeline line/area, split stacked bars, class and infrastructure bars |
| `GET /api/observatory/performance` | — | Active-version saved evaluation + frozen test labels | Binary metrics + typology summary; matrices/per-class **only if present** |
| `GET /api/observatory/features` | `model=binary\|typology` (default binary), `limit=1..46` (default 15) | Active model artifact + manifest feature schema | Horizontal gain-importance bars; group shares |
| `GET /api/observatory/pipeline` | — | Architecture metadata | Directed flowchart |
| `GET /api/observatory/patterns` | — | Conceptual descriptions | Four small illustrative directed diagrams |

`meta` includes `sources: string[]` (repo-relative provenance), `scope`, `dataset_version`, `model_version`, `synthetic: true`, `generated_at` (response timestamp, **not evaluation date**), `notes: string[]`. For dataset and illustrations `model_version` can be `null`; for pipeline/patterns the dataset version can be `null`. The evaluation date is `data.evaluation_date`, sourced from the ML artifact. For V8, performance scope is `saved_test_benchmark`, features scope is `model_artifact`, dataset scope is `bundled_dataset`, and overview's `model_role` is `offline_benchmark`.

### Actual response excerpts (trimmed, not fixture data)

```json
{
  "schema_version": "1.0", "status": "available",
  "meta": {"sources": ["ml/manifests/MANIFEST_v8.json", "ml/reports/binary_metrics_v8.json", "ml/reports/typology_metrics_v8.json", "data/processed/train_blockchain.csv", "data/processed/train_network.csv", "data/processed/test_blockchain.csv", "data/processed/test_network.csv"], "scope": "saved_test_benchmark", "dataset_version": "data/processed", "model_version": "v8", "synthetic": true, "generated_at": "<response UTC time>", "notes": ["Synthetic-data benchmark; these results do not establish real-world detection performance.", "Metrics come from saved evaluation of the active runtime model."]},
  "data": {
    "title": "BitKaun Observatory", "model_role": "offline_benchmark",
    "evaluation_date": "2026-09-08T02:05:00.000000+00:00",
    "transactions": 294693, "scenarios": 5440, "train_scenarios": 4352, "test_scenarios": 1088,
    "features": 46, "binary_model": "binary_model_v8.ubj", "typology_model": "typology_model_v8.ubj",
    "headline_metrics": [{"id": "precision", "label": "PRECISION", "value": 0.9778761061946902, "unit": "ratio"}],
    "formal_decision": null, "sections": ["dataset", "performance", "features", "pipeline", "patterns"]
  }, "message": null
}
```

The `headline_metrics` array has four entries (precision, recall, F1, ROC-AUC); the excerpt shows one. Avoid baking these numeric values into JSX.

```json
{
  "data": {
    "evaluation_date": "2026-09-08T02:05:00.000000+00:00", "evaluation_type": "Saved V8 held-out test metrics",
    "scoring_unit": "scenario", "threshold": 0.5,
    "binary": {"sample_count": 1088, "metrics": [{"id":"precision","label":"PRECISION","value":0.9778761061946902,"unit":"ratio"}], "confusion_matrix": null, "per_class": []},
    "typology": {"sample_count": 448, "metrics": [{"id":"macro_f1","label":"MACRO F1","value":0.9366640164314582,"unit":"ratio"}], "confusion_matrix": null, "per_class": []},
    "diagnostics": [{"id":"calibration","label":"Saved calibration diagnostics","metrics":[{"id":"ece","label":"ECE","value":0.00954160587143098,"unit":"ratio"},{"id":"brier","label":"BRIER","value":0.010557539761066437,"unit":"ratio"}],"note":"Lower is better; saved evaluation scalars."}],
    "formal_decision": null,
    "limitations": ["Synthetic-data benchmark; these results do not establish real-world detection performance.", "V8 reports do not contain confusion matrices or per-class precision/recall; no values are invented."],
    "curves_available": false, "curves_unavailable_reason": "V8 saved reports contain scalar metrics, not ROC/PR coordinates or training history."
  }
}
```

The metric arrays contain more fields than shown; consume them by `id`, not index. Typology `sample_count` is computed from `data/processed/scenario_labels_test.csv` (`is_illicit=1`), because the typology model evaluates only illicit test scenarios. Binary evaluates all test scenarios. The performance threshold comes from the runtime ML service.

## Strong page layout (all values/data driven)

1. **Hero: “Inside the intelligence”** — `overview.data.title`, `meta.model_version`, benchmark date, and four `headline_metrics` cards. Explain that these are held-out synthetic benchmark results.
2. **The dataset** — `dataset.data.totals`, `splits`, activity line chart from `timeline`, scenario class bars from `scenario_class_distribution`, infrastructure bars from `infrastructure_distribution`. Display the scope and provenance. If needed use `transaction_class_distribution` explicitly as **transaction-labelled rows** (different denominator from scenario bars). `scenario_binary_distribution` is licit vs illicit **ground truth**, not predictions. `country_distribution` and `script_distribution` support secondary charts.
3. **How it works** — large flowchart from `pipeline.data.nodes/edges`, preserving returned edge direction, labels, and caveats. Static architecture, not simulated running progress.
4. **Performance** — binary vs typology summary metrics from `performance`; use grouped bars for `precision`/`recall`/`f1` for binary, and `macro_f1`/`accuracy`/`weighted_f1` for typology. Metrics should be labelled separately, not a per-class chart. Show diagnostics and limitations. Only render a confusion heatmap if `confusion_matrix !== null`, with **rows=actual, columns=predicted, exact returned label order**.
5. **What matters to the model** — tabs `features?model=binary` and `?model=typology`. Horizontal bars for `features[].importance`, group bars for `groups[].importance`. Sort order is already descending. The values are normalized *average split gain* for all features; a top-15 list will not sum to 1. Label as **XGBoost gain (global importance)**, never SHAP, probability, or proof of causality. `local_shap_available` is false here. For local case SHAP, the investigator workspace has separate `/alerts/{candidate_id}/evidence` endpoints; do not mix cases into the public benchmark page.
6. **Patterns** — `patterns.data.patterns` has `peeling_chain`, `layering`, `mixing`, `ransomware`. Render their conceptual nodes/edges with an **Illustration** badge, not as real detected wallets or events.
7. **CTA** — link to existing `/terminal` to investigate loaded data.

### Dataset time series semantics

`bucket` defaults to month; allow day/week/month as a selector. `timeline[].timestamp` is the UTC *start* of that bucket. Week starts Monday; interior empty buckets are included with zeros. `transactions` is a transaction count; `output_volume_btc` is sum of all outputs in that bucket, including change and repeat transfers. Label it **transaction output volume (BTC)**, not “illicit BTC”, “unique funds”, or “money laundered”. Naive CSV timestamps are treated as UTC. Use UTC date formatting in the chart to avoid shifting points to the browser's local date.

### TypeScript shape (copy/adapt as desired)

```ts
type Metric = { id: string; label: string; value: number; unit: 'ratio' };
type Item = { id: string; label: string; count: number };
type Meta = {
  sources: string[]; scope: string; dataset_version: string | null;
  model_version: string | null; synthetic: boolean;
  generated_at: string; notes: string[];
};
type Envelope<T> = {
  schema_version: '1.0'; status: 'available' | 'unavailable';
  meta: Meta; data: T | null; message: string | null;
};
type Dataset = {
  totals: { transactions: number; scenarios: number; unique_wallets: number; first_timestamp: string; last_timestamp: string };
  splits: { id: string; label: string; transactions: number; scenarios: number }[];
  bucket: 'day' | 'week' | 'month'; timezone: 'UTC';
  timeline: { timestamp: string; transactions: number; output_volume_btc: number }[];
  scenario_class_distribution: Item[]; scenario_binary_distribution: Item[];
  transaction_class_distribution: Item[]; infrastructure_distribution: Item[];
  country_distribution: Item[]; script_distribution: Item[];
};
type Confusion = { labels: string[]; values: number[][]; row_axis: 'actual'; column_axis: 'predicted' };
type ModelPerformance = {
  sample_count: number; metrics: Metric[];
  confusion_matrix: Confusion | null;
  per_class: { id: string; label: string; precision: number; recall: number; f1: number; support: number; predicted_count: number }[];
};
type Performance = {
  evaluation_date: string; evaluation_type: string; scoring_unit: 'scenario'; threshold: number;
  binary: ModelPerformance; typology: ModelPerformance;
  diagnostics: { id: string; label: string; metrics: Metric[]; note: string }[];
  formal_decision: string | null; limitations: string[];
  curves_available: false; curves_unavailable_reason: string;
};
type Overview = {
  title: string; model_role: 'offline_benchmark'; evaluation_date: string;
  transactions: number; scenarios: number; train_scenarios: number; test_scenarios: number;
  features: number; binary_model: string; typology_model: string;
  headline_metrics: Metric[]; formal_decision: string | null; sections: string[];
};
type Feature = { id: string; label: string; group: string; importance: number };
type Features = {
  model: 'binary' | 'typology'; method: 'normalized_xgboost_gain'; description: string;
  feature_count: number; features: Feature[]; groups: Feature[];
  local_shap_available: false; local_shap_unavailable_reason: string;
};
type Diagram = {
  id: string; label: string; kind: 'architecture' | 'illustration'; description: string;
  nodes: { id: string; label: string; description: string }[];
  edges: { id: string; source: string; target: string; label: string }[];
};
type Patterns = { patterns: Diagram[] };
```

Use `Envelope<Overview>`, `Envelope<Dataset>`, `Envelope<Performance>`, `Envelope<Features>`, `Envelope<Diagram>`, `Envelope<Patterns>` for the six GETs. Check `status === 'available' && data` before reading any chart fields. Empty or missing files return unavailable, not fake zeros. `generated_at` will update per request; do not use it as model training/evaluation date.

## Example chart/data adapters

```ts
// Line/area chart (UTC date and exact backend units)
const points = dataset.timeline.map(p => ({ x: p.timestamp, transactions: p.transactions, btc: p.output_volume_btc }));

// Graph library (React Flow / Cytoscape): stable IDs; no fake amount edges
const nodes = diagram.nodes.map(n => ({ id: n.id, data: { label: n.label, description: n.description } }));
const edges = diagram.edges.map(e => ({ id: e.id, source: e.source, target: e.target, label: e.label }));

// Optional matrix; V8 returns null. Rows actual; columns predicted.
if (performance.binary.confusion_matrix) {
  const { labels, values } = performance.binary.confusion_matrix;
  const cells = values.flatMap((row, actual) => row.map((count, predicted) => ({ actual: labels[actual], predicted: labels[predicted], count })));
}
```

For progressive rendering fetch the small overview/pipeline/patterns/performance endpoints immediately; fetch dataset as a separate loading panel (its first aggregation can take seconds, subsequent calls are cached by file fingerprint). Fetch gain chart only when its section is visible if desired; first access inspects the local artifact. Use concise independent skeletons and per-panel retry buttons. Disable chart controls while their specific request is loading.

## Verification and handoff checklist

1. `python -B -m unittest backend.tests.test_observatory -q` from the repo root checks version selection, exact V8 metric provenance, dataset UTC aggregation, corrupt artifacts, cache refresh, model gain, diagrams and validation.
2. Open `/openapi.json` for the complete generated response schemas; spot-check `GET /api/observatory/overview`, `GET /api/observatory/performance`, `GET /api/observatory/dataset?bucket=month` and `GET /api/observatory/features?model=binary` while backend runs.
3. Render `meta.model_version` and `meta.synthetic` near performance, use `data.evaluation_date` on benchmark cards, and show backend `limitations` and chart unavailability explanations visibly.
4. Confirm direct `/analytics` refresh on both Vite and FastAPI production static serving, plus navigation back to landing and terminal.

Implementation: `backend/app/api/routes_observatory.py`, `backend/app/services/observatory_service.py`, `backend/app/services/observatory_diagrams.py`, `backend/app/models/observatory.py`. This contract describes the shipped response models, not the old `/eval/benchmark` prototype endpoint.
