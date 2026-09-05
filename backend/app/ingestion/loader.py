"""
Master Data Loader for SIH PS146 Bitcoin AML Dataset (v2.0).
Loads and merges blockchain transactions with P2P network telemetry.
"""
import logging
import pandas as pd
from pathlib import Path
from backend.app.core.config import (
    BLOCKCHAIN_CSV_PATH,
    NETWORK_CSV_PATH,
    settings
)
from backend.app.ingestion.parser import parse_and_enrich_dataframe

logger = logging.getLogger(__name__)

def load_master_dataset(
    blockchain_path: Path = BLOCKCHAIN_CSV_PATH,
    network_path: Path = NETWORK_CSV_PATH
) -> pd.DataFrame:
    """
    Loads master on-chain and network metadata CSV files, performs an inner join on txid,
    parses JSON array fields, and validates data integrity.
    
    Returns:
        pd.DataFrame: Merged and parsed DataFrame containing all 82,078 transactions.
    """
    if not blockchain_path.exists():
        raise FileNotFoundError(f"Blockchain ledger file not found at: {blockchain_path}")
    if not network_path.exists():
        raise FileNotFoundError(f"Network telemetry file not found at: {network_path}")

    logger.info(f"Loading blockchain ledger from: {blockchain_path}")
    df_chain = pd.read_csv(blockchain_path)
    
    logger.info(f"Loading network telemetry from: {network_path}")
    df_net = pd.read_csv(network_path)

    logger.info(f"Joining {len(df_chain)} blockchain rows with {len(df_net)} network rows on 'txid'...")
    df_merged = pd.merge(df_chain, df_net, on="txid", suffixes=("", "_net"))

    # Deduplicate redundant scenario_id / split columns from network table
    for duplicate_col in ["scenario_id_net", "split_net"]:
        if duplicate_col in df_merged.columns:
            df_merged.drop(columns=[duplicate_col], inplace=True)

    # Parse JSON arrays and enrich with timing deltas
    logger.info("Parsing multi-I/O JSON array columns and calculating propagation latency...")
    df_unified = parse_and_enrich_dataframe(df_merged)

    # Sanity checks
    row_count = len(df_unified)
    logger.info(f"Successfully loaded and parsed {row_count} transactions.")
    
    if row_count != settings.EXPECTED_TOTAL_ROWS:
        logger.warning(
            f"Row count ({row_count}) differs from expected count ({settings.EXPECTED_TOTAL_ROWS})"
        )
        
    return df_unified
