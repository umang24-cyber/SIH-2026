"""
Application Configuration and Path Constants.
Uses pathlib.Path exclusively for cross-platform (WSL2 / Linux / Windows) compatibility.
"""
from pathlib import Path
from pydantic import BaseModel

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Master Data Files (v2.0)
BLOCKCHAIN_CSV_PATH = DATA_PROCESSED_DIR / "blockchain_transactions.csv"
NETWORK_CSV_PATH = DATA_PROCESSED_DIR / "network_metadata.csv"

# Pre-split Files
TRAIN_BLOCKCHAIN_PATH = DATA_PROCESSED_DIR / "train_blockchain.csv"
TRAIN_NETWORK_PATH = DATA_PROCESSED_DIR / "train_network.csv"
TEST_BLOCKCHAIN_PATH = DATA_PROCESSED_DIR / "test_blockchain.csv"
TEST_NETWORK_PATH = DATA_PROCESSED_DIR / "test_network.csv"

class Settings(BaseModel):
    APP_NAME: str = "BitKaun AML Forensics API"
    APP_VERSION: str = "2.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["*"]
    
    # Expected record count
    EXPECTED_TOTAL_ROWS: int = 96251

settings = Settings()
