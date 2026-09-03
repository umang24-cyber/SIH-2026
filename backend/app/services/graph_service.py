"""
Graph Analytics & Link-Analysis Service.
Constructs heterogeneous subgraphs (Wallet, Tx, IP) and performs multi-hop BFS path tracing.
"""
import networkx as nx
import logging
from typing import Optional, List, Dict, Any, Set
from collections import deque
from backend.app.services.data_service import data_service
from backend.app.models.schemas import (
    GraphResponse,
    GraphNode,
    GraphEdge,
    TraceResponse,
    TraceHop
)

logger = logging.getLogger(__name__)

class GraphService:
    def build_scenario_graph(self, scenario_id: str) -> GraphResponse:
        """
        Constructs a heterogeneous graph for a specific scenario per Section 7 of DATA_DICTIONARY.md.
        - Nodes: Wallet, Transaction, IP
        - Edges: SENT, RECEIVED, BROADCAST
        """
        txids = data_service.get_scenario_txids(scenario_id)
        nodes_map: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []
        
        for txid in txids:
            tx = data_service.txid_map.get(txid)
            if not tx:
                continue
                
            tx_node_id = f"tx_{txid}"
            
            # 1. Transaction Node
            if tx_node_id not in nodes_map:
                nodes_map[tx_node_id] = GraphNode(
                    id=tx_node_id,
                    type="Transaction",
                    properties={
                        "txid": txid,
                        "timestamp": str(tx["timestamp"]),
                        "fee_btc": float(tx["fee_btc"]),
                        "script_type": str(tx["script_type"]),
                        "scenario_id": scenario_id
                    }
                )
                
            # 2. Input Wallets & SENT Edges
            for idx, (in_addr, in_amt) in enumerate(zip(tx["input_addresses"], tx["input_amounts"])):
                if in_addr not in nodes_map:
                    # Check if licit exchange
                    is_exc = len(data_service.address_in_map.get(in_addr, [])) >= 50
                    nodes_map[in_addr] = GraphNode(
                        id=in_addr,
                        type="Wallet",
                        properties={
                            "address": in_addr,
                            "is_licit_exchange": is_exc
                        }
                    )
                    
                edge_id = f"sent_{in_addr}_{txid}_{idx}"
                edges.append(GraphEdge(
                    id=edge_id,
                    source=in_addr,
                    target=tx_node_id,
                    type="SENT",
                    properties={"amount_btc": round(float(in_amt), 8)}
                ))
                
            # 3. Output Wallets & RECEIVED Edges
            for idx, (out_addr, out_amt) in enumerate(zip(tx["output_addresses"], tx["output_amounts"])):
                if out_addr not in nodes_map:
                    is_exc = len(data_service.address_out_map.get(out_addr, [])) >= 50
                    nodes_map[out_addr] = GraphNode(
                        id=out_addr,
                        type="Wallet",
                        properties={
                            "address": out_addr,
                            "is_licit_exchange": is_exc
                        }
                    )
                    
                edge_id = f"recv_{txid}_{out_addr}_{idx}"
                edges.append(GraphEdge(
                    id=edge_id,
                    source=tx_node_id,
                    target=out_addr,
                    type="RECEIVED",
                    properties={"amount_btc": round(float(out_amt), 8)}
                ))
                
            # 4. IP Relay Node & BROADCAST Edge
            relay_ip = str(tx.get("relay_ip", ""))
            if relay_ip:
                ip_node_id = f"ip_{relay_ip}"
                if ip_node_id not in nodes_map:
                    nodes_map[ip_node_id] = GraphNode(
                        id=ip_node_id,
                        type="IP",
                        properties={
                            "relay_ip": relay_ip,
                            "country_code": str(tx.get("country_code", "US")),
                            "asn": str(tx.get("asn", "")),
                            "isp": str(tx.get("isp", "")),
                            "node_type": str(tx.get("node_type", "residential")),
                            "relay_port": int(tx.get("relay_port", 8333))
                        }
                    )
                    
                edge_id = f"broad_{relay_ip}_{txid}"
                edges.append(GraphEdge(
                    id=edge_id,
                    source=ip_node_id,
                    target=tx_node_id,
                    type="BROADCAST",
                    properties={
                        "relay_timestamp": str(tx.get("relay_timestamp", "")),
                        "relay_port": int(tx.get("relay_port", 8333)),
                        "user_agent": str(tx.get("user_agent", ""))
                    }
                ))

        return GraphResponse(
            scenario_id=scenario_id,
            nodes=list(nodes_map.values()),
            edges=edges
        )

    def find_trace_path(self, src: str, dst: str, max_depth: int = 6) -> TraceResponse:
        """
        Executes Breadth-First Search (BFS) over Bitcoin transaction chains
        from source address to destination address up to max_depth hops.
        """
        if src not in data_service.unique_wallets or dst not in data_service.unique_wallets:
            return TraceResponse(
                source_address=src,
                destination_address=dst,
                path_found=False,
                hop_count=0,
                total_transferred_btc=0.0,
                hops=[]
            )

        # BFS Queue holds: (current_wallet, path_of_hops, visited_wallets, accumulated_btc)
        # Hop: {"from_wallet", "to_wallet", "txid", "amount_btc", "timestamp", "flagged_typology"}
        queue = deque([(src, [], {src}, 0.0)])
        
        while queue:
            curr_wallet, hops, visited, total_btc = queue.popleft()
            
            if curr_wallet == dst and hops:
                return TraceResponse(
                    source_address=src,
                    destination_address=dst,
                    path_found=True,
                    hop_count=len(hops),
                    total_transferred_btc=round(total_btc, 8),
                    hops=[TraceHop(**h) for h in hops]
                )
                
            if len(hops) >= max_depth:
                continue
                
            # Outgoing transactions where curr_wallet is an input address
            outgoing_txids = data_service.address_in_map.get(curr_wallet, [])
            for txid in outgoing_txids:
                tx = data_service.txid_map.get(txid)
                if not tx:
                    continue
                    
                timestamp = str(tx.get("timestamp", ""))
                
                # Check output addresses created by this tx
                for out_addr, out_amt in zip(tx["output_addresses"], tx["output_amounts"]):
                    if out_addr not in visited:
                        new_hop = {
                            "hop_index": len(hops) + 1,
                            "from_wallet": curr_wallet,
                            "to_wallet": out_addr,
                            "txid": txid,
                            "amount_btc": round(float(out_amt), 8),
                            "timestamp": timestamp,
                            "flagged_typology": tx.get("pattern_type") if tx.get("is_illicit") == 1 else None
                        }
                        
                        queue.append((
                            out_addr,
                            hops + [new_hop],
                            visited | {out_addr},
                            total_btc + out_amt
                        ))

        return TraceResponse(
            source_address=src,
            destination_address=dst,
            path_found=False,
            hop_count=0,
            total_transferred_btc=0.0,
            hops=[]
        )

# Global Singleton Instance
graph_service = GraphService()
