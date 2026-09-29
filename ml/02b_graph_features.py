"""
02b_graph_features.py
=====================
Day 2 — Graph Feature Fallback (no P4 dependency).

Builds a per-scenario networkx.DiGraph from array columns and extracts
topological features. P4's features can be merged on top later if delivered.

Run from SIH-2026/:
    conda activate ml
    python ml/02b_graph_features.py

Outputs:
    data/processed/scenario_graph_features_train.csv
    data/processed/scenario_graph_features_test.csv
"""

import json
import warnings
from collections import deque
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"

ARRAY_COLS = ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]


def load_blockchain(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in ARRAY_COLS:
        df[col] = df[col].apply(json.loads)
    return df


def sep(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def compute_graph_features(grp: pd.DataFrame) -> dict:
    """
    Build a bipartite DiGraph for one scenario and extract topological features.

    Graph structure:
      input_address  --(SENT edge, weight=amount)--> txid_node
      txid_node      --(RECEIVED edge, weight=amount)--> output_address

    Node naming convention to avoid collisions between addresses and txids:
      Address nodes: prefix "addr_"
      Transaction nodes: prefix "tx_"

    For 1-2 txn scenarios (most ransomware), many features collapse to trivial
    values (density≈1, chain_length=1, clustering=0). This IS the discriminative
    signal — small-scenario structure indicates ransomware, NOT a bug.
    """
    G = nx.DiGraph()
    cycle_detected = False

    addr_nodes = set()

    columns = ["txid", "input_addresses", "input_amounts", "output_addresses", "output_amounts"]
    for txid, input_addresses, input_amounts, output_addresses, output_amounts in grp[columns].itertuples(index=False, name=None):
        tx_node = f"tx_{txid}"
        G.add_node(tx_node, node_class="tx")

        for addr, amt in zip(input_addresses, input_amounts):
            anode = f"addr_{addr}"
            addr_nodes.add(anode)
            G.add_node(anode, node_class="addr")
            G.add_edge(anode, tx_node, weight=float(amt))

        for addr, amt in zip(output_addresses, output_amounts):
            anode = f"addr_{addr}"
            addr_nodes.add(anode)
            G.add_node(anode, node_class="addr")
            G.add_edge(tx_node, anode, weight=float(amt))

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()

    # edge_to_node_ratio
    edge_to_node_ratio = n_edges / n_nodes if n_nodes > 0 else 0.0

    # graph_density
    graph_density = nx.density(G)

    # max_chain_length — longest simple path length
    # Use dag_longest_path_length if DAG, else BFS fallback with depth limit 15.
    # B3 FIX: Pass weight=None to dag_longest_path_length so it counts hops, not amounts.
    if nx.is_directed_acyclic_graph(G):
        try:
            max_chain_length = nx.dag_longest_path_length(G, weight=None)
        except Exception:
            max_chain_length = 1
    else:
        # Cycle detected — should be rare given address reuse is one-directional
        # Fall back to BFS with depth limit 15
        cycle_detected = True
        max_depth = 0
        for node in G.nodes():
            visited = {node}
            queue = deque([(node, 0)])
            while queue:
                cur, depth = queue.popleft()
                if depth > max_depth:
                    max_depth = depth
                if max_depth == 15:
                    break  # 15 is the exact upper bound of this fallback.
                if depth < 15:
                    for nxt in G.successors(cur):
                        if nxt not in visited:
                            visited.add(nxt)
                            queue.append((nxt, depth + 1))
            if max_depth == 15:
                break
        max_chain_length = max_depth
        
    # Divide by 2 because bipartite graph has 2 edges per transaction (addr->tx->addr)
    max_chain_length = max_chain_length // 2

    # avg_clustering — on address-only one-mode projection (NOT the raw bipartite graph).
    # IMPORTANT: avg_clustering on any bipartite graph's undirected form is ALWAYS 0.0
    # because triangles cannot exist in a bipartite graph (addr and tx nodes are disjoint
    # sets, so no addr-addr-addr triangle can close). The one-mode projection connects
    # address nodes that share at least one transaction, which CAN form triangles.
    # B2 FIX: compute clustering on the address-to-address co-occurrence graph.
    G_addr_proj = nx.Graph()
    G_addr_proj.add_nodes_from(addr_nodes)
    for tx_node in [n for n in G.nodes() if n.startswith("tx_")]:
        coparticipants = (
            [p for p in G.predecessors(tx_node) if p.startswith("addr_")] +
            [s for s in G.successors(tx_node)   if s.startswith("addr_")]
        )
        for i in range(len(coparticipants)):
            for j in range(i + 1, len(coparticipants)):
                G_addr_proj.add_edge(coparticipants[i], coparticipants[j])
    avg_clustering = (
        nx.average_clustering(G_addr_proj)
        if G_addr_proj.number_of_nodes() > 0
        else 0.0
    )

    # max_in_degree, max_out_degree — address nodes only (filter out tx_ nodes)
    addr_in_degrees  = [G.in_degree(n)  for n in addr_nodes if G.has_node(n)]
    addr_out_degrees = [G.out_degree(n) for n in addr_nodes if G.has_node(n)]
    max_in_degree  = int(max(addr_in_degrees))  if addr_in_degrees  else 0
    max_out_degree = int(max(addr_out_degrees)) if addr_out_degrees else 0

    # degree_assortativity — NaN or ±inf for uniform-degree graphs (e.g. single-txn
    # scenarios) or degenerate star graphs. Guard with isfinite (catches NaN AND ±inf).
    try:
        da = nx.degree_assortativity_coefficient(G)
        degree_assortativity = float(da) if (da is not None and np.isfinite(da)) else 0.0
    except Exception:
        degree_assortativity = 0.0

    return {
        "max_chain_length":      int(max_chain_length),
        "graph_density":         float(graph_density),
        "avg_clustering":        float(avg_clustering),
        "max_in_degree":         max_in_degree,
        "max_out_degree":        max_out_degree,
        "degree_assortativity":  degree_assortativity,
        "edge_to_node_ratio":    float(edge_to_node_ratio),
        "_cycle_detected":       int(cycle_detected),
    }


def process_split(bc_path: Path, split_name: str):
    sep(f"Processing graph features: {split_name}")
    df = load_blockchain(bc_path)
    n_scenarios = df["scenario_id"].nunique()
    print(f"  {len(df):,} rows, {n_scenarios:,} scenarios")

    rows = []
    cycles_found = 0
    for i, (scenario_id, grp) in enumerate(df.groupby("scenario_id")):
        feat = compute_graph_features(grp)
        feat["scenario_id"] = scenario_id
        if feat.pop("_cycle_detected"):
            cycles_found += 1
        rows.append(feat)
        if (i + 1) % 2000 == 0:
            print(f"    ... {i+1:,}/{n_scenarios:,} scenarios processed")

    result = pd.DataFrame(rows)
    print(f"  Done. Shape: {result.shape}")
    print(f"  Cycles detected: {cycles_found} (fallback BFS used)")
    print(f"  NaN counts:\n{result.isnull().sum().to_string()}")
    return result


def run_pipeline():
    """Build and persist graph features for the train and test splits."""
    train_graph = process_split(DATA / "train_blockchain.csv", "train")
    test_graph  = process_split(DATA / "test_blockchain.csv", "test")

    train_path = DATA / "scenario_graph_features_train.csv"
    test_path  = DATA / "scenario_graph_features_test.csv"
    train_graph.to_csv(train_path, index=False)
    test_graph.to_csv(test_path, index=False)

    print(f"\nSaved: {train_path}  ({len(train_graph):,} rows)")
    print(f"Saved: {test_path}   ({len(test_graph):,} rows)")
    sep("DONE — 02b_graph_features.py")


if __name__ == "__main__":
    run_pipeline()
