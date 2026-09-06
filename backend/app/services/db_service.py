"""
Database Service for BitKaun Forensics.
Handles persistent storage of transactions, dossiers, and audit logs.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from backend.app.db.database import get_db_connection, init_db
from backend.app.db.schema import create_schema

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        self._initialized = False

    def ensure_initialized(self) -> None:
        """Ensures database file, connection, and schema are ready."""
        if not self._initialized:
            init_db()
            create_schema()
            self._initialized = True

    # -------------------------------------------------------------------------
    # TRANSACTIONS CRUD
    # -------------------------------------------------------------------------
    def save_transaction(self, record: Dict[str, Any], is_custom: bool = True) -> None:
        """Persists a single normalized transaction into SQLite."""
        self.ensure_initialized()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO forensic_transactions (
                    txid, timestamp, relay_timestamp, input_addresses, output_addresses,
                    input_amounts, output_amounts, fee_btc, script_type, scenario_id,
                    relay_ip, relay_port, node_type, country_code, asn, isp,
                    user_agent, propagation_delta_ms, is_custom_ingested
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(txid) DO UPDATE SET
                    timestamp=excluded.timestamp,
                    relay_timestamp=excluded.relay_timestamp,
                    input_addresses=excluded.input_addresses,
                    output_addresses=excluded.output_addresses,
                    input_amounts=excluded.input_amounts,
                    output_amounts=excluded.output_amounts,
                    fee_btc=excluded.fee_btc,
                    script_type=excluded.script_type,
                    scenario_id=excluded.scenario_id,
                    relay_ip=excluded.relay_ip,
                    relay_port=excluded.relay_port,
                    node_type=excluded.node_type,
                    country_code=excluded.country_code,
                    asn=excluded.asn,
                    isp=excluded.isp,
                    user_agent=excluded.user_agent,
                    propagation_delta_ms=excluded.propagation_delta_ms,
                    is_custom_ingested=excluded.is_custom_ingested;
                """,
                (
                    int(record["txid"]),
                    str(record.get("timestamp", "2026-09-06 12:00:00")),
                    str(record.get("relay_timestamp", record.get("timestamp", "2026-09-06 12:00:00"))),
                    json.dumps(record.get("input_addresses", [])),
                    json.dumps(record.get("output_addresses", [])),
                    json.dumps(record.get("input_amounts", [])),
                    json.dumps(record.get("output_amounts", [])),
                    float(record.get("fee_btc", 0.0001)),
                    str(record.get("script_type", "P2PKH")),
                    str(record.get("scenario_id", f"custom_{record['txid']}")),
                    str(record.get("relay_ip", "127.0.0.1")),
                    int(record.get("relay_port", 8333)),
                    str(record.get("node_type", "residential")),
                    str(record.get("country_code", "US")),
                    str(record.get("asn", "AS15169")),
                    str(record.get("isp", "Standard Relay ISP")),
                    str(record.get("user_agent", "/Satoshi:22.0.0/")),
                    float(record.get("propagation_delta_ms", 0.0)),
                    1 if is_custom else 0,
                )
            )
            conn.commit()

    def save_transactions_batch(self, records: List[Dict[str, Any]], is_custom: bool = True) -> int:
        """Bulk inserts or updates transactions using a single transaction block."""
        self.ensure_initialized()
        if not records:
            return 0

        rows = []
        for record in records:
            rows.append((
                int(record["txid"]),
                str(record.get("timestamp", "2026-09-06 12:00:00")),
                str(record.get("relay_timestamp", record.get("timestamp", "2026-09-06 12:00:00"))),
                json.dumps(record.get("input_addresses", [])),
                json.dumps(record.get("output_addresses", [])),
                json.dumps(record.get("input_amounts", [])),
                json.dumps(record.get("output_amounts", [])),
                float(record.get("fee_btc", 0.0001)),
                str(record.get("script_type", "P2PKH")),
                str(record.get("scenario_id", f"custom_{record['txid']}")),
                str(record.get("relay_ip", "127.0.0.1")),
                int(record.get("relay_port", 8333)),
                str(record.get("node_type", "residential")),
                str(record.get("country_code", "US")),
                str(record.get("asn", "AS15169")),
                str(record.get("isp", "Standard Relay ISP")),
                str(record.get("user_agent", "/Satoshi:22.0.0/")),
                float(record.get("propagation_delta_ms", 0.0)),
                1 if is_custom else 0,
            ))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO forensic_transactions (
                    txid, timestamp, relay_timestamp, input_addresses, output_addresses,
                    input_amounts, output_amounts, fee_btc, script_type, scenario_id,
                    relay_ip, relay_port, node_type, country_code, asn, isp,
                    user_agent, propagation_delta_ms, is_custom_ingested
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(txid) DO UPDATE SET
                    timestamp=excluded.timestamp,
                    relay_timestamp=excluded.relay_timestamp,
                    input_addresses=excluded.input_addresses,
                    output_addresses=excluded.output_addresses,
                    input_amounts=excluded.input_amounts,
                    output_amounts=excluded.output_amounts,
                    fee_btc=excluded.fee_btc,
                    script_type=excluded.script_type,
                    scenario_id=excluded.scenario_id,
                    relay_ip=excluded.relay_ip,
                    relay_port=excluded.relay_port,
                    node_type=excluded.node_type,
                    country_code=excluded.country_code,
                    asn=excluded.asn,
                    isp=excluded.isp,
                    user_agent=excluded.user_agent,
                    propagation_delta_ms=excluded.propagation_delta_ms,
                    is_custom_ingested=excluded.is_custom_ingested;
                """,
                rows
            )
            conn.commit()
        return len(rows)

    def load_all_custom_transactions(self) -> List[Dict[str, Any]]:
        """Loads all custom-ingested transactions from SQLite to hydrate in-memory index on boot."""
        self.ensure_initialized()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM forensic_transactions WHERE is_custom_ingested = 1 ORDER BY txid ASC;")
            rows = cursor.fetchall()
            
            results = []
            for r in rows:
                results.append({
                    "txid": r["txid"],
                    "timestamp": r["timestamp"],
                    "relay_timestamp": r["relay_timestamp"],
                    "input_addresses": json.loads(r["input_addresses"]),
                    "output_addresses": json.loads(r["output_addresses"]),
                    "input_amounts": json.loads(r["input_amounts"]),
                    "output_amounts": json.loads(r["output_amounts"]),
                    "fee_btc": r["fee_btc"],
                    "script_type": r["script_type"],
                    "scenario_id": r["scenario_id"],
                    "relay_ip": r["relay_ip"],
                    "relay_port": r["relay_port"],
                    "node_type": r["node_type"],
                    "country_code": r["country_code"],
                    "asn": r["asn"],
                    "isp": r["isp"],
                    "user_agent": r["user_agent"],
                    "propagation_delta_ms": r["propagation_delta_ms"],
                })
            return results

    # -------------------------------------------------------------------------
    # DOSSIERS CRUD
    # -------------------------------------------------------------------------
    def save_dossier(self, dossier: Dict[str, Any]) -> None:
        """Saves or updates a structured investigative summary."""
        self.ensure_initialized()
        meta = dossier.get("case_metadata", {})
        dossier_id = str(meta.get("dossier_id", f"LEA-STR-{dossier.get('txid', 'UNKNOWN')}"))
        txid = int(dossier.get("txid", 0))
        scenario_id = str(dossier.get("scenario_id", meta.get("scenario_id", "UNKNOWN")))
        target_entity = str(meta.get("target_entity", f"TX:{txid}"))
        case_status = str(meta.get("case_status", "ACTIVE_INVESTIGATION"))
        risk_level = str(dossier.get("forensic_risk_assessment", {}).get("risk_category", "HIGH"))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lea_dossiers (
                    dossier_id, txid, scenario_id, target_entity, case_status, risk_level, content_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dossier_id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    target_entity=excluded.target_entity,
                    case_status=excluded.case_status,
                    risk_level=excluded.risk_level,
                    content_json=excluded.content_json;
                """,
                (dossier_id, txid, scenario_id, target_entity, case_status, risk_level, json.dumps(dossier))
            )
            conn.commit()

    def get_dossier(self, dossier_id_or_txid: str) -> Optional[Dict[str, Any]]:
        """Retrieves a stored dossier by ID or numeric TXID."""
        self.ensure_initialized()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if dossier_id_or_txid.isdigit():
                cursor.execute("SELECT content_json FROM lea_dossiers WHERE txid = ? ORDER BY created_at DESC LIMIT 1;", (int(dossier_id_or_txid),))
            else:
                cursor.execute("SELECT content_json FROM lea_dossiers WHERE dossier_id = ? LIMIT 1;", (dossier_id_or_txid,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["content_json"])
            return None

    def list_all_dossiers(self) -> List[Dict[str, Any]]:
        """Lists metadata for all saved LEA court dossiers."""
        self.ensure_initialized()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dossier_id, txid, scenario_id, target_entity, case_status, risk_level, created_at FROM lea_dossiers ORDER BY created_at DESC;")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # AUDIT LOGS CRUD
    # -------------------------------------------------------------------------
    def log_ingestion_audit(self, filename: str, file_type: str, total_records: int, scenario_clusters: List[str]) -> None:
        """Records an immutable forensic audit trail for uploaded files."""
        self.ensure_initialized()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ingestion_audit_logs (filename, file_type, total_records, scenario_clusters)
                VALUES (?, ?, ?, ?);
                """,
                (filename, file_type, total_records, ", ".join(scenario_clusters))
            )
            conn.commit()

db_service = DBService()
