"""
Community & Syndicate Detection Service.
Partitions transaction subgraphs into modular communities using NetworkX algorithms.
Runs 100% offline in-memory.
"""
import networkx as nx
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.graph_service import graph_service

logger = logging.getLogger(__name__)

class CommunityService:
    def detect_communities(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        Executes modularity-based community detection on the scenario's transaction graph.
        Partitions wallets and transactions into distinct sub-clusters / syndicates.
        """
        graph_resp = graph_service.build_scenario_graph(scenario_id)
        if not graph_resp.nodes:
            return None

        # Build undirected NetworkX graph for modularity analysis
        G = nx.Graph()
        for node in graph_resp.nodes:
            props = dict(node.properties)
            props["graph_node_type"] = node.type
            G.add_node(node.id, **props)

        for edge in graph_resp.edges:
            edge_props = dict(edge.properties)
            edge_props["graph_edge_type"] = edge.type
            G.add_edge(edge.source, edge.target, **edge_props)

        # Run Greedy Modularity Community Detection
        communities_list = []
        try:
            communities = nx.community.greedy_modularity_communities(G)
            for comm_idx, comm_set in enumerate(communities, start=1):
                nodes_in_comm = []
                wallets_count = 0
                txs_count = 0
                ips_count = 0

                for node_id in comm_set:
                    node_data = G.nodes[node_id]
                    ntype = node_data.get("graph_node_type", "Unknown")
                    if ntype == "Wallet":
                        wallets_count += 1
                    elif ntype == "Transaction":
                        txs_count += 1
                    elif ntype == "IP":
                        ips_count += 1

                    nodes_in_comm.append({
                        "id": node_id,
                        "type": ntype
                    })

                communities_list.append({
                    "community_id": f"comm_{scenario_id}_{comm_idx}",
                    "total_members": len(comm_set),
                    "wallet_count": wallets_count,
                    "transaction_count": txs_count,
                    "ip_count": ips_count,
                    "members": nodes_in_comm[:20]  # Preview top 20
                })
        except Exception as e:
            logger.warning(f"Community detection fallback for {scenario_id}: {e}")
            communities_list.append({
                "community_id": f"comm_{scenario_id}_all",
                "total_members": len(G.nodes),
                "wallet_count": sum(1 for n in G.nodes if G.nodes[n].get("graph_node_type") == "Wallet"),
                "transaction_count": sum(1 for n in G.nodes if G.nodes[n].get("graph_node_type") == "Transaction"),
                "ip_count": sum(1 for n in G.nodes if G.nodes[n].get("graph_node_type") == "IP"),
                "members": [{"id": n, "type": G.nodes[n].get("graph_node_type", "Unknown")} for n in list(G.nodes)[:20]]
            })

        return {
            "scenario_id": scenario_id,
            "total_nodes": len(graph_resp.nodes),
            "total_edges": len(graph_resp.edges),
            "total_communities_detected": len(communities_list),
            "communities": communities_list
        }

# Global Singleton Instance
community_service = CommunityService()
