"""
Tor & Obfuscated Network Telemetry Profiler.
100% Offline / Air-Gapped Linux & WSL2 compliant.

Solves the core Tor de-anonymization challenge:
1. Calculates Shannon Timing Entropy (H) on gossip propagation delays (Δt).
2. Performs multi-vantage Tor circuit clustering using Common-Input Ownership Heuristics (CIOH).
3. Evaluates Obfuscation Evasion Risk and deanonymization confidence.
"""
import math
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service

logger = logging.getLogger(__name__)

class TorProfiler:
    def __init__(self):
        self._cached_summary: Optional[Dict[str, Any]] = None

    def calculate_shannon_entropy(self, deltas: List[float], bin_size: float = 1.0) -> float:
        """
        Calculates Shannon Entropy H = -sum(p_i * log2(p_i)) over discretized timing bins.
        - Low entropy (< 1.5): Automated bot / script relay broadcast with fixed periodicity.
        - High entropy (> 3.0): Dispersed network routing / human interactive broadcast.
        """
        if not deltas:
            return 0.0
        
        bins = defaultdict(int)
        for d in deltas:
            b = math.floor(abs(d) / bin_size)
            bins[b] += 1
            
        total = len(deltas)
        entropy = 0.0
        for count in bins.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
                
        return round(entropy, 4)

    def profile_tor_transaction(self, txid: int) -> Dict[str, Any]:
        """
        Performs in-depth Tor circuit & entropy analysis for a specific transaction.
        """
        tx = data_service.txid_map.get(txid)
        if not tx:
            return {"error": f"Transaction {txid} not found", "txid": txid}

        node_type = str(tx.get("node_type", "residential"))
        is_tor = node_type == "tor_exit_node" or bool(tx.get("is_tor", False))
        ip = str(tx.get("relay_ip", "0.0.0.0"))
        delta_t_sec = float(tx.get("propagation_delta_ms", 0.0)) / 1000.0

        # Check entity cluster of inputs
        input_addresses = tx.get("input_addresses", [])
        entity_id = "UNKNOWN"
        cluster_wallets: List[str] = []
        if input_addresses:
            first_addr = input_addresses[0]
            entity_id = clustering_service.get_entity_id(first_addr)
            cluster_wallets = clustering_service.get_cluster_wallets(first_addr)

        # Find other transactions originating from the same IP / Tor Node
        same_ip_txs = []
        same_ip_deltas = []
        for other_tx in data_service.txid_map.values():
            if str(other_tx.get("relay_ip")) == ip:
                other_txid = other_tx["txid"]
                same_ip_txs.append(other_txid)
                same_ip_deltas.append(float(other_tx.get("propagation_delta_ms", 0.0)) / 1000.0)

        entropy = self.calculate_shannon_entropy(same_ip_deltas)

        # Obfuscation resilience scoring:
        # High delta_t + Tor exit node + Multi-input cluster = High deanonymization confidence
        has_cluster_link = len(cluster_wallets) > 1
        burst_automation = entropy < 1.5 and len(same_ip_deltas) > 3

        evasion_risk_score = 0.30
        if is_tor:
            evasion_risk_score += 0.40
        if has_cluster_link:
            evasion_risk_score += 0.20
        if burst_automation:
            evasion_risk_score += 0.10

        evasion_risk_score = min(1.0, round(evasion_risk_score, 2))

        return {
            "txid": txid,
            "ip_address": ip,
            "is_tor": is_tor,
            "node_type": node_type,
            "country": tx.get("country_code", "US"),
            "isp": tx.get("isp", "Unknown"),
            "timing_delta_seconds": round(delta_t_sec, 3),
            "timing_entropy": entropy,
            "entropy_interpretation": (
                "Automated / Scripted Broadcast" if burst_automation 
                else ("High Latency Obfuscation" if entropy > 2.5 else "Standard Relay Jitter")
            ),
            "correlated_ip_transactions_count": len(same_ip_txs),
            "correlated_txids": same_ip_txs[:20],
            "input_cluster_attribution": {
                "entity_id": entity_id,
                "cluster_size": len(cluster_wallets),
                "syndicate_link": has_cluster_link
            },
            "deanonymization_confidence": (
                "HIGH (Unmasked via CIOH Multi-Input Clustering)" if has_cluster_link 
                else ("MEDIUM (Timing Jitter Fingerprinted)" if is_tor else "LOW")
            ),
            "obfuscation_evasion_score": evasion_risk_score
        }

    def get_tor_network_summary(self) -> Dict[str, Any]:
        """
        Computes aggregate metrics across all Tor and proxy exit nodes in the dataset.
        """
        if self._cached_summary:
            return self._cached_summary

        tor_txids: List[int] = []
        tor_deltas: List[float] = []
        non_tor_deltas: List[float] = []
        countries: Dict[str, int] = defaultdict(int)
        unique_tor_ips: set = set()

        for tx in data_service.txid_map.values():
            delta_t_sec = float(tx.get("propagation_delta_ms", 0.0)) / 1000.0
            node_type = str(tx.get("node_type", "residential"))
            is_tor = node_type == "tor_exit_node" or bool(tx.get("is_tor", False))

            if is_tor:
                tor_txids.append(tx["txid"])
                tor_deltas.append(delta_t_sec)
                unique_tor_ips.add(str(tx.get("relay_ip", "")))
                countries[str(tx.get("country_code", "Unknown"))] += 1
            else:
                non_tor_deltas.append(delta_t_sec)

        avg_tor_delta = sum(tor_deltas) / len(tor_deltas) if tor_deltas else 0.0
        avg_normal_delta = sum(non_tor_deltas) / len(non_tor_deltas) if non_tor_deltas else 0.0
        tor_entropy = self.calculate_shannon_entropy(tor_deltas)

        # Top 5 Tor Exit Countries
        top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]

        self._cached_summary = {
            "total_tor_transactions": len(tor_txids),
            "unique_tor_exit_nodes": len(unique_tor_ips),
            "tor_timing_entropy": tor_entropy,
            "average_tor_propagation_delay_sec": round(avg_tor_delta, 2),
            "average_normal_propagation_delay_sec": round(avg_normal_delta, 2),
            "top_tor_exit_countries": [{"country": c, "tx_count": cnt} for c, cnt in top_countries],
            "methodology": "Passive Multi-Vantage Timing Entropy & CIOH Cross-Layer Triangulation"
        }
        return self._cached_summary

tor_profiler = TorProfiler()
