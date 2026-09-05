"""
Scenario Forensics & Risk Profiling Service.
Computes deep structural metrics, infrastructure risk, and dominant laundering typologies for scenario clusters.
Runs 100% offline in-memory.
"""
import logging
from typing import Dict, Any, Optional, List
from collections import Counter
from backend.app.services.data_service import data_service

logger = logging.getLogger(__name__)

class ScenarioService:
    def get_scenario_detail(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        Calculates comprehensive forensic profile for a scenario cluster:
        - Financial volume and fee aggregates
        - Unique entities, wallets, and relay infrastructure
        - Infrastructure risk score (0-100%)
        - Dominant heuristic typology
        - Hub wallets (highest transaction degree)
        """
        txids = data_service.get_scenario_txids(scenario_id)
        if not txids:
            return None

        tx_list = [data_service.txid_map[t] for t in txids if t in data_service.txid_map]
        if not tx_list:
            return None

        total_in_btc = 0.0
        total_out_btc = 0.0
        total_fee_btc = 0.0
        wallets = set()
        ips = set()
        asns = set()
        countries = set()
        node_types = []
        script_types = []
        latencies = []
        timestamps = []
        wallet_degrees = Counter()

        for tx in tx_list:
            in_addrs = tx.get("input_addresses", [])
            out_addrs = tx.get("output_addresses", [])
            in_amts = tx.get("input_amounts", [])
            out_amts = tx.get("output_amounts", [])
            
            total_in_btc += sum(in_amts)
            total_out_btc += sum(out_amts)
            total_fee_btc += float(tx.get("fee_btc", 0.0))

            for addr in in_addrs:
                wallets.add(addr)
                wallet_degrees[addr] += 1
            for addr in out_addrs:
                wallets.add(addr)
                wallet_degrees[addr] += 1

            ip = tx.get("relay_ip", "")
            if ip:
                ips.add(ip)
            asn = tx.get("asn", "")
            if asn:
                asns.add(asn)
            cc = tx.get("country_code", "")
            if cc:
                countries.add(cc)

            node_types.append(tx.get("node_type", "residential"))
            script_types.append(tx.get("script_type", "P2PKH"))
            latencies.append(float(tx.get("propagation_delta_ms", 0.0)))
            timestamps.append(str(tx.get("timestamp", "")))

        # Infrastructure risk score: higher if bulletproof_host, tor_exit_node, vpn_proxy
        high_risk_infra_count = sum(1 for nt in node_types if nt in ["bulletproof_host", "tor_exit_node", "vpn_proxy"])
        infra_risk_score = round((high_risk_infra_count / max(1, len(node_types))) * 100.0, 2)

        # Dominant Typology Heuristic
        dominant_typology = "normal"
        if scenario_id.startswith("peel"):
            dominant_typology = "peeling_chain"
        elif scenario_id.startswith("layer"):
            dominant_typology = "layering"
        elif scenario_id.startswith("mix"):
            dominant_typology = "mixing"
        elif scenario_id.startswith("ransom"):
            dominant_typology = "ransomware"
        elif infra_risk_score >= 50.0:
            dominant_typology = "suspicious_network_routing"

        sorted_times = sorted(timestamps)
        start_time = sorted_times[0] if sorted_times else ""
        end_time = sorted_times[-1] if sorted_times else ""

        top_hubs = [
            {"address": addr, "degree": deg}
            for addr, deg in wallet_degrees.most_common(5)
        ]

        return {
            "scenario_id": scenario_id,
            "dominant_typology": dominant_typology,
            "infrastructure_risk_score": infra_risk_score,
            "transaction_count": len(tx_list),
            "unique_wallets_count": len(wallets),
            "unique_relay_ips_count": len(ips),
            "total_input_volume_btc": round(total_in_btc, 8),
            "total_output_volume_btc": round(total_out_btc, 8),
            "total_fees_btc": round(total_fee_btc, 8),
            "average_propagation_delta_ms": round(sum(latencies) / max(1, len(latencies)), 2),
            "time_window": {
                "start": start_time,
                "end": end_time
            },
            "infrastructure_breakdown": dict(Counter(node_types)),
            "origin_asns": sorted(list(asns)),
            "origin_countries": sorted(list(countries)),
            "script_type_distribution": dict(Counter(script_types)),
            "top_hub_wallets": top_hubs,
            "member_txids": txids[:50]
        }

# Global Singleton Instance
scenario_service = ScenarioService()
