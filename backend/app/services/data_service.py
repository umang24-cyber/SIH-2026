"""
In-Memory Data Service for Sub-Millisecond Forensic Queries.
Loads 82,078 transactions once at server startup and builds address & scenario indexes.
"""
import time
import logging
import pandas as pd
from typing import Optional, Dict, Any, List
from collections import defaultdict
from backend.app.ingestion.loader import load_master_dataset
from backend.app.models.schemas import EntityResponse, TransactionResponse, NetworkTelemetry
from backend.app.services.db_service import db_service

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.txid_map: Dict[int, Dict[str, Any]] = {}
        self.address_in_map: Dict[str, List[int]] = defaultdict(list)
        self.address_out_map: Dict[str, List[int]] = defaultdict(list)
        self.scenario_tx_map: Dict[str, List[int]] = defaultdict(list)
        self.unique_wallets: set = set()
        self.start_time: float = time.time()
        self.is_ready: bool = False

    def initialize(self):
        """Loads master dataset and builds reverse indexes for instant lookups."""
        if self.is_ready:
            return
        logger.info("Initializing in-memory forensic data store...")
        t0 = time.time()
        self.df = load_master_dataset()
        
        # Build in-memory fast lookup indexes from master dataset
        logger.info("Indexing addresses and scenario clusters...")
        records = self.df.to_dict(orient="records")
        for rec in records:
            txid = rec["txid"]
            self.txid_map[txid] = rec
            
            # Map scenarios
            sc_id = rec.get("scenario_id", "")
            if sc_id:
                self.scenario_tx_map[sc_id].append(txid)
                
            # Map input addresses
            for in_addr in rec.get("input_addresses", []):
                self.address_in_map[in_addr].append(txid)
                self.unique_wallets.add(in_addr)
                
            # Map output addresses
            for out_addr in rec.get("output_addresses", []):
                self.address_out_map[out_addr].append(txid)
                self.unique_wallets.add(out_addr)

        # Hydrate all persisted custom transactions from SQLite database
        try:
            persisted_custom_txs = db_service.load_all_custom_transactions()
            for r in persisted_custom_txs:
                self._index_transaction_memory(r)
            if persisted_custom_txs:
                logger.info(f"Restored {len(persisted_custom_txs)} custom transactions from persistent SQLite DB.")
        except Exception as exc:
            logger.warning(f"Could not load custom transactions from SQLite on boot: {exc}")

        elapsed = time.time() - t0
        self.is_ready = True
        logger.info(
            f"Data store ready! Indexed {len(self.txid_map)} transactions, "
            f"{len(self.unique_wallets)} unique wallets, "
            f"{len(self.scenario_tx_map)} scenarios in {elapsed:.2f}s."
        )

    def get_transaction(self, txid: int) -> Optional[TransactionResponse]:
        """Look up full dual-layer transaction by txid."""
        rec = self.txid_map.get(txid)
        if not rec:
            return None
            
        return TransactionResponse(
            txid=rec["txid"],
            timestamp=str(rec["timestamp"]),
            input_addresses=rec["input_addresses"],
            output_addresses=rec["output_addresses"],
            input_amounts=rec["input_amounts"],
            output_amounts=rec["output_amounts"],
            fee_btc=float(rec["fee_btc"]),
            script_type=str(rec["script_type"]),
            scenario_id=str(rec["scenario_id"]),
            network=NetworkTelemetry(
                relay_timestamp=str(rec.get("relay_timestamp", "")),
                relay_ip=str(rec.get("relay_ip", "")),
                relay_port=int(rec.get("relay_port", 8333)),
                node_type=str(rec.get("node_type", "residential")),
                country_code=str(rec.get("country_code", "US")),
                asn=str(rec.get("asn", "")),
                isp=str(rec.get("isp", "")),
                protocol_version=int(rec.get("protocol_version", 70015)),
                user_agent=str(rec.get("user_agent", "/Satoshi:22.0.0/")),
                propagation_delta_ms=float(rec.get("propagation_delta_ms", 0.0))
            )
        )

    def get_entity(self, address: str) -> Optional[EntityResponse]:
        """Compute wallet profile, financial flows, and exchange status for an address."""
        sent_txids = self.address_in_map.get(address, [])
        recv_txids = self.address_out_map.get(address, [])
        all_txids = set(sent_txids + recv_txids)
        
        if not all_txids:
            return None
            
        total_sent = 0.0
        total_received = 0.0
        timestamps = []
        scenarios = set()
        
        # Calculate sent volume
        for txid in sent_txids:
            tx = self.txid_map[txid]
            timestamps.append(tx["timestamp"])
            scenarios.add(tx.get("scenario_id", ""))
            for in_addr, in_amt in zip(tx["input_addresses"], tx["input_amounts"]):
                if in_addr == address:
                    total_sent += in_amt
                    
        # Calculate received volume
        for txid in recv_txids:
            tx = self.txid_map[txid]
            timestamps.append(tx["timestamp"])
            scenarios.add(tx.get("scenario_id", ""))
            for out_addr, out_amt in zip(tx["output_addresses"], tx["output_amounts"]):
                if out_addr == address:
                    total_received += out_amt

        sorted_times = sorted(timestamps)
        first_seen = sorted_times[0] if sorted_times else ""
        last_seen = sorted_times[-1] if sorted_times else ""
        
        # 30 planted exchange wallets have tx_count >= 50 and high volume
        tx_count = len(all_txids)
        is_exchange = tx_count >= 50 and (total_sent > 100.0 or total_received > 100.0)

        return EntityResponse(
            address=address,
            is_licit_exchange=is_exchange,
            total_received_btc=round(total_received, 8),
            total_sent_btc=round(total_sent, 8),
            tx_count=tx_count,
            first_seen=first_seen,
            last_seen=last_seen,
            associated_scenarios=sorted(list(scenarios))
        )

    def get_scenario_txids(self, scenario_id: str) -> List[int]:
        """Return all txids belonging to a specific scenario."""
        return self.scenario_tx_map.get(scenario_id, [])

    def _index_transaction_memory(self, record: Dict[str, Any]) -> None:
        """Internal helper to index a transaction dictionary into memory maps."""
        txid = int(record["txid"])
        self.txid_map[txid] = record

        sc_id = str(record.get("scenario_id") or f"custom_{txid}")
        if sc_id not in self.scenario_tx_map:
            self.scenario_tx_map[sc_id] = []
        if txid not in self.scenario_tx_map[sc_id]:
            self.scenario_tx_map[sc_id].append(txid)

        in_addrs = record.get("input_addresses", [])
        out_addrs = record.get("output_addresses", [])

        for in_a in in_addrs:
            self.address_in_map[in_a].append(txid)
            self.unique_wallets.add(in_a)

        for out_a in out_addrs:
            self.address_out_map[out_a].append(txid)
            self.unique_wallets.add(out_a)

    def add_transaction(self, record: Dict[str, Any]) -> bool:
        """Dynamically indexes a new transaction into memory and persists to SQLite."""
        txid = int(record["txid"])
        if txid in self.txid_map:
            return False
        self._index_transaction_memory(record)
        try:
            db_service.save_transaction(record, is_custom=True)
        except Exception as exc:
            logger.warning(f"Could not persist transaction {record.get('txid')} to SQLite: {exc}")
        return True

    def add_transactions_batch(self, records: List[Dict[str, Any]]) -> int:
        """Batch-indexes new transactions in memory and persists to SQLite."""
        new_records = []
        for r in records:
            txid = int(r["txid"])
            if txid in self.txid_map:
                continue
            self._index_transaction_memory(r)
            new_records.append(r)
        try:
            db_service.save_transactions_batch(new_records, is_custom=True)
        except Exception as exc:
            logger.warning(f"Could not batch-persist {len(new_records)} transactions to SQLite: {exc}")
        return len(new_records)

    def get_stats(self) -> Dict[str, Any]:
        """Return high-level memory store telemetry."""
        return {
            "loaded_transactions": len(self.txid_map),
            "unique_scenarios": len(self.scenario_tx_map),
            "unique_wallets": len(self.unique_wallets),
            "uptime_seconds": round(time.time() - self.start_time, 2)
        }

# Global Singleton Instance
data_service = DataService()
