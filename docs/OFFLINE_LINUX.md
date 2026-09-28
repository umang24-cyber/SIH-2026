# Linux offline delivery — BitKaun

Target: Ubuntu x86_64 with Python **3.11 or 3.12** (including `venv`/`ensurepip`) and a WebGL-capable browser already present. A complete offline *runtime* never calls an external API, registry or CDN. Preparation/building the USB bundle is a separate, connected-machine step. Match the preparation host's architecture, Python minor version, distro/runtime libraries and ML wheel compatibility to the target; Windows wheels/venvs are not portable to Linux.

## Build the transfer bundle (connected Linux preparation machine)

Have the V8 model files and matching local dataset in the checkout. Run from the repository root:

```bash
PYTHON_BIN=python3.12 bash scripts/build_offline_bundle.sh
```

The builder downloads binary Python wheels and CLI wheel into `offline_bundle/BitKaun-linux-x86_64/wheelhouse`, builds the existing React/Three.js frontend once, and copies the backend, built `dist`, fonts/audio, docs/source citations, V8 artifacts, datasets and scripts. The output is ignored by git. **Transfer the whole directory, not only `dist`.** If a wheel cannot be built/downloaded for the chosen Linux/Python, the build fails on the preparation host; do not attempt network fallback on the air-gapped machine.

The builder then installs those wheels **with `--no-index` into a clean temporary environment**, runs the real runtime verification with remote connections denied, and emits `requirements.lock.txt`, `runtime-verification.json`, and SHA-256 `bundle-manifest.json`. The installer checks hashes and the Python minor version/CPU architecture, then installs the exact locked versions. The bundled Isolation Forest requires **scikit-learn 1.9.0**; a different pickle runtime version fails the verification gate. Linux uses the official CPU-only XGBoost distribution, avoiding unneeded CUDA/NCCL downloads. A previously built frontend can be reused with `BITKAUN_USE_PREBUILT_FRONTEND=1`; otherwise the builder runs `npm ci` and `npm run build`.

An optional full-graph export at `public/data/graph_export.json`, if present on the preparation host, is copied to `dist/data/`; the 3D bulk graph loader needs that file. It is not in the repository by default. Scenario graphs from the local API are independent of that bulk export. Do not claim the optional 3D bulk view works unless you ship and test its export.

## Install and run (air-gapped target)

```bash
cd BitKaun-linux-x86_64
bash scripts/install_offline.sh
bash run_ubuntu.sh
```

The installer creates a local `.venv`, forces `PIP_NO_INDEX=1`, and installs only from the included wheelhouse. A target machine must already have Python 3.11/3.12 with venv/ensurepip and a browser; for a fresh Linux installation those **OS packages and native libraries must themselves be pre-provisioned offline**. No `npm`, Node.js or internet is needed to run the built app. The launcher requires the preinstalled Python environment and `dist/index.html`, performs a local dependency preflight, then serves the frontend and API on `http://127.0.0.1:8000` (loopback only). Cases/reports continue to use BitKaun's user-writable local app data directory. Stop with Ctrl+C.

The local API reference is `/docs`, with no CDN. The machine-readable schema is `/openapi.json`; Field Guide citation links are served by `/source/...` locally. `http://127.0.0.1` is loopback, not an external internet request. Offline analysis operates on bundled or uploaded records; it cannot fetch new live Bitcoin data without a separately supplied feed.

## Acceptance check on the exact target

1. Disconnect internet and disable browser cache (or use a new browser profile); **do not just disconnect after visiting the page once**.
2. Run installer/startup from the transferred directory. Open `/`, `/analytics`, `/docs`, `/openapi.json`, and a Field Guide source citation. Check DevTools Network for failed assets and external requests (expected hosts: only `127.0.0.1`).
3. Upload ledger + network CSVs, inspect exact-ID coverage, unmatched rows and timing anomalies, inspect scenario V8 ML and SHAP results, open the API-backed transaction graph, and export a dossier. Repeat after restart to confirm SQLite persistence.
4. Test any optional bulk Three.js view **only if** the export was bundled. Confirm WebGL support on the actual GPU/browser.
5. Record the target OS, Python version, package versions, test dataset, build hash, and result. This repository cannot certify an untested Linux target in advance.

Verification on a development machine: `python -B -m pytest backend/tests/test_offline_delivery.py backend/tests/test_correlation_evidence.py`, `npm run build`, and `bash -n run_ubuntu.sh scripts/build_offline_bundle.sh scripts/install_offline.sh`. A connected build alone is not an offline runtime proof.

For the complete runtime check, use `python -B scripts/verify_offline_runtime.py`. It creates a temporary database (`BITKAUN_DATA_DIR`) and checks real model loading, actual Observatory responses, sample CSV correlation with ML and anomaly inference, uploaded scenario graph, and HTML dossier export. It denies remote Python socket connections and DNS resolution. The first dossier may trigger the full local alert scan and take several minutes.

For the browser check, use `npx playwright test --config playwright.offline.config.ts` after provisioning the test browser on the preparation machine. It starts the actual backend, uses a fresh browser context, blocks all non-local browser requests and service workers, checks local fonts/docs/source links and real analytics, and submits a real dual-stream sample through the terminal UI. Linux backend verification and browser visual/GPU verification are separate checks; the test browser is not a runtime application dependency.

### Recorded checks for this checkout

- WSL Ubuntu x86_64, Python 3.12.14: clean-wheelhouse build, source/hash manifest verification, `--no-index` bundle install, startup with real V8 model and Isolation Forest, real sample correlation/ML, scenario graph and HTML export **passed** with external Python connections and DNS denied. Results: `offline_bundle/BitKaun-linux-x86_64/runtime-verification.json` (generated, git-ignored).
- Built frontend: Chromium/Playwright browser test with non-local browser requests blocked: landing, docs, local source citation, all six real Observatory endpoints, two-stream upload/evidence **passed**. This test used a Windows browser against the local backend; it does not prove Linux GPU/WebGL compatibility.
- This is a Linux x86_64 / Python 3.12 bundle, not a portable AppImage or a completely bootstrapped Linux OS. A native target machine must have a matching Python interpreter, OS libraries and a WebGL-capable browser provisioned beforehand; verify that exact target independently.
