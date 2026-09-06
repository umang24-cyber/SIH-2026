"""
Forensic SQLite Database Schema Definitions & Indexing.
"""
import sqlite3
import logging
from backend.app.db.database import get_db_connection

logger = logging.getLogger(__name__)

CREATE_TABLES_SQL = """
-- 1. Forensic Transactions Table
CREATE TABLE IF NOT EXISTS forensic_transactions (
    txid INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    relay_timestamp TEXT NOT NULL,
    input_addresses TEXT NOT NULL,      -- JSON Array of string addresses
    output_addresses TEXT NOT NULL,     -- JSON Array of string addresses
    input_amounts TEXT NOT NULL,        -- JSON Array of float amounts
    output_amounts TEXT NOT NULL,       -- JSON Array of float amounts
    fee_btc REAL DEFAULT 0.0001,
    script_type TEXT DEFAULT 'P2PKH',
    scenario_id TEXT NOT NULL,
    relay_ip TEXT DEFAULT '127.0.0.1',
    relay_port INTEGER DEFAULT 8333,
    node_type TEXT DEFAULT 'residential',
    country_code TEXT DEFAULT 'US',
    asn TEXT DEFAULT 'AS15169',
    isp TEXT DEFAULT 'Standard Relay ISP',
    user_agent TEXT DEFAULT '/Satoshi:22.0.0/',
    propagation_delta_ms REAL DEFAULT 0.0,
    is_custom_ingested INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for lightning fast graph and clustering lookups
CREATE INDEX IF NOT EXISTS idx_tx_scenario ON forensic_transactions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_tx_node_type ON forensic_transactions(node_type);
CREATE INDEX IF NOT EXISTS idx_tx_relay_ip ON forensic_transactions(relay_ip);
CREATE INDEX IF NOT EXISTS idx_tx_custom ON forensic_transactions(is_custom_ingested);

-- 2. Investigation summaries table
CREATE TABLE IF NOT EXISTS lea_dossiers (
    dossier_id TEXT PRIMARY KEY,
    txid INTEGER NOT NULL,
    scenario_id TEXT NOT NULL,
    target_entity TEXT NOT NULL,
    case_status TEXT DEFAULT 'ACTIVE_INVESTIGATION',
    risk_level TEXT DEFAULT 'HIGH',
    content_json TEXT NOT NULL,         -- Full structured investigative summary JSON
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(txid) REFERENCES forensic_transactions(txid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dossier_txid ON lea_dossiers(txid);
CREATE INDEX IF NOT EXISTS idx_dossier_scenario ON lea_dossiers(scenario_id);
CREATE INDEX IF NOT EXISTS idx_dossier_created ON lea_dossiers(created_at);

-- 3. File Upload & Ingestion Audit Log Table
CREATE TABLE IF NOT EXISTS ingestion_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    total_records INTEGER NOT NULL,
    scenario_clusters TEXT NOT NULL,    -- Comma-separated or JSON list of cluster IDs
    ingested_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_ingested_at ON ingestion_audit_logs(ingested_at);
"""

def create_schema() -> None:
    """Executes schema definition scripts and creates all forensic indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(CREATE_TABLES_SQL)
        conn.commit()
    logger.info("Forensic SQLite Database schema & indexes created successfully.")
