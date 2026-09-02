# Environment & Setup Guide — SIH PS146

## 1. System Requirements & Target Environment

- **Target Operating System:** Ubuntu 24.04 LTS (Native Linux or Windows WSL2)
- **Python Runtime:** Python 3.11 or Python 3.12
- **Node.js Runtime:** Node.js 20.x+ and npm 10.x+ (for frontend dashboard)
- **Offline / Air-Gapped Note:** The system is designed to run entirely offline without external internet access during demonstration or forensic analysis.
- **GeoIP Resolution Note:** MaxMind GeoLite2 telemetry is **already resolved and pre-assigned** in the v2.0 dataset (`country_code`, `asn`, and `isp` columns per `DATA_DICTIONARY.md` Section 2b). **No runtime GeoIP binary or lookup daemon is required.**

---

## 2. WSL2 / Linux Setup Instructions

### Step 1: Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl build-essential
```

### Step 2: Set Up Python Virtual Environment
```bash
# Navigate to project repository
cd /path/to/SIH-2026

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 3: Install Python Dependencies

Create or use `requirements.txt` containing core project libraries:

```text
# Data & Math
pandas>=2.2.0
numpy>=1.26.0

# Graph Analytics
networkx>=3.2.0

# Machine Learning & Explainability
scikit-learn>=1.4.0
xgboost>=2.0.0
lightgbm>=4.3.0
shap>=0.45.0

# Backend REST API
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0

# Testing & Verification
pytest>=8.0.0
```

Install via pip:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Frontend Setup (React Dashboard)

```bash
# From the repository root
npm install

# Start local frontend development server
npm run dev
```

---

## 4. Verification & Validation Step

To verify that the dataset files, Python environment, and data parsing are functioning correctly, run the dataset integrity validation script:

```bash
# Ensure virtual environment is active
python data_pipeline/validate_v2.py
```

### Expected Output
The script checks all 15 integrity rules against `data/processed/blockchain_transactions.csv` and `data/processed/network_metadata.csv`:
- Row Count Match (82,078 rows)
- Key Alignment on `txid` (0 orphans)
- No duplicate transaction IDs
- Valid timing (`relay_timestamp <= timestamp`)
- Zero null values across all columns
- Valid JSON array parsing for `input_addresses`, `output_addresses`, `input_amounts`, `output_amounts`
- Accounting identity satisfaction (`sum(inputs) == sum(outputs) + fee_btc`)
- Deterministic 80/20 train/test scenario split integrity (zero scenario leakage)

All 15 checks should report `✅ PASS`.
