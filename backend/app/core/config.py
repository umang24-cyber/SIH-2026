"""
Application Configuration and Path Constants.
Uses pathlib.Path exclusively for cross-platform (WSL2 / Linux / Windows) compatibility.
"""
import os
import platform
from pathlib import Path
from pydantic import BaseModel

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Data directories with V8 priority
DATA_PROCESSED_V8_DIR = BASE_DIR / "data" / "processed_v8"
DATA_PROCESSED_DIR = DATA_PROCESSED_V8_DIR if DATA_PROCESSED_V8_DIR.exists() else (BASE_DIR / "data" / "processed")

def get_app_data_dir() -> Path:
    """Returns the OS-specific local application data directory.
    Under WSL2, automatically discovers the shared Windows AppData directory so
    Windows PowerShell and Ubuntu WSL share the exact same physical folder.
    """
    system = platform.system()
    if system == "Windows":
        app_data = os.getenv("LOCALAPPDATA")
        if not app_data:
            app_data = os.path.expanduser("~\\AppData\\Local")
        return Path(app_data) / "BitKaun"
    else:
        # Check if running in WSL2 with accessible Windows mount
        win_users = Path("/mnt/c/Users")
        if win_users.is_dir():
            for u in win_users.iterdir():
                target = u / "AppData" / "Local" / "BitKaun"
                if target.is_dir():
                    return target
        return Path.home() / ".local" / "share" / "BitKaun"

APP_DATA_DIR = get_app_data_dir()
REPORTS_DIR = APP_DATA_DIR / "reports"
CASES_DIR = APP_DATA_DIR / "cases"
CASES_DIR.mkdir(parents=True, exist_ok=True)

# Master Data Files (V8)
BLOCKCHAIN_CSV_PATH = DATA_PROCESSED_DIR / "blockchain_transactions.csv"
NETWORK_CSV_PATH = DATA_PROCESSED_DIR / "network_metadata.csv"

# Pre-split Files
TRAIN_BLOCKCHAIN_PATH = DATA_PROCESSED_DIR / "train_blockchain.csv"
TRAIN_NETWORK_PATH = DATA_PROCESSED_DIR / "train_network.csv"
TEST_BLOCKCHAIN_PATH = DATA_PROCESSED_DIR / "test_blockchain.csv"
TEST_NETWORK_PATH = DATA_PROCESSED_DIR / "test_network.csv"

class Settings(BaseModel):
    APP_NAME: str = "BitKaun AML Forensics API (v8.0 Forensic Engine)"
    APP_VERSION: str = "8.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["*"]
    
    # Expected record count in V8 dataset (294,639 transactions across 5,440 scenarios)
    EXPECTED_TOTAL_ROWS: int = 294639

settings = Settings()
