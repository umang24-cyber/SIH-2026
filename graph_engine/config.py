"""
config.py — Central configuration for the graph engine.

All tunables and file paths live here. Downstream modules import from this
module; nothing is hard-coded elsewhere.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Project root (two levels up from this file: graph_engine/ → SIH-2026/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"

BLOCKCHAIN_CSV = DATA_DIR / "blockchain_transactions.csv"
NETWORK_CSV    = DATA_DIR / "network_metadata.csv"

GRAPH_EXPORT_JSON       = OUTPUT_DIR / "graph_export.json"
ML_HANDOFF_CSV          = OUTPUT_DIR / "candidates_ml_handoff.csv"
VALIDATION_REPORT_JSON  = OUTPUT_DIR / "validation_report.json"

# ---------------------------------------------------------------------------
# Graph-build
# ---------------------------------------------------------------------------

# Node-ID prefixes keep wallet / transaction / IP ID spaces disjoint
PREFIX_WALLET = "w:"
PREFIX_TX     = "tx:"
PREFIX_IP     = "ip:"

# ---------------------------------------------------------------------------
# Peeling-chain detector tunables
# ---------------------------------------------------------------------------

# Maximum seconds allowed between consecutive hops in a chain
PEEL_MAX_HOP_GAP_SECONDS: int = 6 * 3600          # 6 hours

# Minimum number of hops to accept as a peeling-chain candidate
PEEL_MIN_CHAIN_LENGTH: int = 3

# The "carry-forward" output in a peel tx is the one with the larger amount.
# This tolerance (fraction) allows for slight amount inversions at a hop
# due to fee structure without discarding the chain.
PEEL_AMOUNT_TOLERANCE: float = 0.05               # 5 % tolerance

# Minimum ratio between carry-forward output amount and peeled amount
# carry_amt / peeled_amt must be >= this to be considered an asymmetric peel
PEEL_MIN_ASYMMETRY_RATIO: float = 2.0

# Minimum decay-consistency score (0.5 * monotonicity + 0.5 * log-linear R^2)
PEEL_MIN_DECAY_SCORE: float = 0.6

# ---------------------------------------------------------------------------
# Layering detector tunables
# ---------------------------------------------------------------------------

# Minimum out-degree (wallet-to-wallet projection) to consider fan-out
LAYER_MIN_FANOUT_DEGREE: int = 5

# Maximum hops to follow forward when looking for reconvergence
LAYER_MAX_RECONVERGENCE_HOPS: int = 3

# Fraction of fan-out recipients that must reconverge for a hit
LAYER_MIN_RECONVERGENCE_RATIO: float = 0.6

# Maximum seconds from first fan-out tx to last fan-in tx
LAYER_MAX_TIME_WINDOW_SECONDS: int = 72 * 3600    # 72 hours

# Maximum time gap between consecutive hops in a layering branch
LAYER_MAX_HOP_GAP_SECONDS: int = LAYER_MAX_TIME_WINDOW_SECONDS  # 72 hours

# Wallets appearing in more transactions than this are treated as exchange-like
# hubs and excluded from being a convergence sink
LAYER_EXCHANGE_DEGREE_THRESHOLD: int = 500

# ---------------------------------------------------------------------------
# Mixing (Louvain community) detector tunables
# ---------------------------------------------------------------------------

# Minimum inputs AND outputs for a tx to be included in the co-participation
# graph (filters out simple 1-in-1-out or 1-in-2-out txs)
MIX_MIN_INPUTS:  int = 3
MIX_MIN_OUTPUTS: int = 3

# Minimum community size (wallets) to report
MIX_MIN_COMMUNITY_SIZE: int = 5

# Internal density threshold
MIX_MIN_DENSITY: float = 0.30

# External connectivity ratio ceiling
MIX_MAX_EXTERNAL_RATIO: float = 0.40

# Output amount coefficient-of-variation ceiling (uniform amounts → low CV)
MIX_MAX_AMOUNT_CV: float = 0.50

# Maximum seconds spanning all txs in a mixing cluster
MIX_MAX_TIME_WINDOW_SECONDS: int = 48 * 3600      # 48 hours

# Louvain random seed for reproducibility
LOUVAIN_RANDOM_STATE: int = 42

# ---------------------------------------------------------------------------
# Suspicious infrastructure node_type values (for tor_vpn_fraction feature)
# ---------------------------------------------------------------------------

SUSPICIOUS_NODE_TYPES: frozenset[str] = frozenset({
    "tor_exit_node",
    "vpn_proxy",
    "bulletproof_host",
})

# ---------------------------------------------------------------------------
# Validation — true-positive threshold
# ---------------------------------------------------------------------------

# A detected candidate is a TP if at least this fraction of its member txids
# share the matching ground-truth pattern_type
VALIDATION_TP_THRESHOLD: float = 0.80
