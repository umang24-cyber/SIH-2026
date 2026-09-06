"""
Common-Input Ownership Heuristic (CIOH) Multi-Input Clustering Engine.
Clusters Bitcoin addresses into real-world Entity IDs using Disjoint Set Union (DSU).
Runs 100% offline in-memory without external database calls.
"""
import logging
from typing import Dict, Set, List, Optional
from collections import defaultdict
from backend.app.services.data_service import data_service
from backend.app.models.schemas import ClusterResponse

logger = logging.getLogger(__name__)

class DisjointSetUnion:
    def __init__(self):
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = defaultdict(int)

    def find(self, x: str) -> str:
        """Find representative with full path compression."""
        if x not in self.parent:
            self.parent[x] = x
            return x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str):
        """Union by rank."""
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return

        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

class ClusteringService:
    def __init__(self):
        self.dsu = DisjointSetUnion()
        self.cluster_members: Dict[str, Set[str]] = defaultdict(set)
        self.cluster_multi_tx_count: Dict[str, int] = defaultdict(int)
        self.is_clustered: bool = False

    def build_clusters(self):
        """Scans all multi-input transactions and clusters co-spending addresses."""
        if not data_service.is_ready:
            data_service.initialize()

        logger.info("Executing Common-Input Ownership Heuristic (CIOH) clustering...")
        multi_input_count = 0

        # Pass 1: Union all co-inputs
        for tx in data_service.txid_map.values():
            inputs = tx.get("input_addresses", [])
            if len(inputs) >= 2:
                multi_input_count += 1
                base_addr = inputs[0]
                for next_addr in inputs[1:]:
                    self.dsu.union(base_addr, next_addr)

        # Pass 2: Group all known wallets into their root clusters
        for addr in data_service.unique_wallets:
            root = self.dsu.find(addr)
            self.cluster_members[root].add(addr)

        self.is_clustered = True
        logger.info(
            f"CIOH Clustering complete! Analyzed {multi_input_count} multi-input transactions. "
            f"Partitioned {len(data_service.unique_wallets)} addresses into {len(self.cluster_members)} entity clusters."
        )

    def get_entity_cluster(self, address: str) -> Optional[ClusterResponse]:
        """Look up the co-owned cluster for any Bitcoin address."""
        if not self.is_clustered:
            self.build_clusters()

        if address not in data_service.unique_wallets:
            return None

        root = self.dsu.find(address)
        members = sorted(list(self.cluster_members.get(root, {address})))
        
        # Calculate aggregated cluster financials
        total_recv = 0.0
        total_sent = 0.0
        scenarios = set()
        multi_tx_count = 0

        for member in members:
            # Add sent volume
            for txid in data_service.address_in_map.get(member, []):
                tx = data_service.txid_map.get(txid)
                if tx:
                    scenarios.add(tx.get("scenario_id", ""))
                    if len(tx.get("input_addresses", [])) >= 2:
                        multi_tx_count += 1
                    for in_a, in_amt in zip(tx["input_addresses"], tx["input_amounts"]):
                        if in_a == member:
                            total_sent += in_amt

            # Add received volume
            for txid in data_service.address_out_map.get(member, []):
                tx = data_service.txid_map.get(txid)
                if tx:
                    scenarios.add(tx.get("scenario_id", ""))
                    for out_a, out_amt in zip(tx["output_addresses"], tx["output_amounts"]):
                        if out_a == member:
                            total_recv += out_amt

        # Compute 8-dimensional graph structural topological embedding
        import math
        vec = [
            math.log1p(len(members)),
            math.log1p(total_recv),
            math.log1p(total_sent),
            float(multi_tx_count) / max(1, len(members)),
            float(len(scenarios)),
            math.log1p(sum(len(data_service.address_in_map.get(m, [])) for m in members)),
            math.log1p(sum(len(data_service.address_out_map.get(m, [])) for m in members)),
            abs(total_recv - total_sent) / max(0.0001, total_recv + total_sent)
        ]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        embedding = [round(x / norm, 4) for x in vec]

        return ClusterResponse(
            query_address=address,
            cluster_id=f"entity_{root[:12]}",
            cluster_size=len(members),
            co_owned_addresses=members[:50],  # Top 50 members preview
            total_cluster_received_btc=round(total_recv, 8),
            total_cluster_sent_btc=round(total_sent, 8),
            multi_input_tx_count=multi_tx_count,
            associated_scenarios=sorted(list(scenarios)),
            clustering_method="CIOH + Graph Structural Embedding",
            cluster_embedding=embedding
        )

    def get_entity_id(self, address: str) -> str:
        """Returns the canonical entity cluster ID for an address."""
        if not self.is_clustered:
            self.build_clusters()
        root = self.dsu.find(address)
        return f"entity_{root[:12]}" if root else f"entity_{address[:12]}"

    def get_cluster_wallets(self, address: str) -> List[str]:
        """Returns all wallet addresses belonging to the same entity cluster."""
        if not self.is_clustered:
            self.build_clusters()
        root = self.dsu.find(address)
        return sorted(list(self.cluster_members.get(root, {address})))

# Global Singleton Instance
clustering_service = ClusteringService()
