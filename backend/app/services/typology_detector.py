"""
Algorithmic Typology Detection Engine for Bitcoin Forensic Graph Analytics.
Implements structural heuristics for:
1. Peeling Chains (1->2 out change address reuse traversal)
2. Layering (Fan-out N -> Fan-in N reconvergence)
3. CoinJoin Mixing (N->N equal-denomination anonymization)
4. Ransomware Payment Aggregation
"""
import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from collections import Counter, defaultdict
from backend.app.models.schemas import AlertSummary, FeatureAttribution, EvidenceResponse
from backend.app.services.data_service import data_service

logger = logging.getLogger(__name__)

class TypologyDetector:
    def __init__(self):
        self.detected_alerts: List[AlertSummary] = []
        self.evidence_cache: Dict[str, EvidenceResponse] = {}
        self._attribution_attempted: Set[str] = set()
        self.tx_typology_map: Dict[int, List[str]] = defaultdict(list)
        self.is_scanned: bool = False

    def scan_all_typologies(self):
        """Run scenario-level heuristic detectors and cache their alerts.

        Each detector emits at most one alert per scenario. These heuristic
        alerts are independent of the ML typology classifier.
        """
        if not data_service.is_ready:
            data_service.initialize()
            
        logger.info("Running algorithmic typology detection heuristics across all scenarios...")
        self.evidence_cache.clear()
        self._attribution_attempted.clear()
        alerts = []
        
        # 1. Detect Peeling Chains
        peel_alerts = self._detect_peeling_chains()
        alerts.extend(peel_alerts)
        logger.info(f"Detected {len(peel_alerts)} peeling chain candidate structures.")

        # 2. Detect Layering (Fan-Out -> Fan-In Reconvergence)
        layer_alerts = self._detect_layering()
        alerts.extend(layer_alerts)
        logger.info(f"Detected {len(layer_alerts)} layering candidate structures.")

        # 3. Detect Mixing / CoinJoin Pools
        mix_alerts = self._detect_mixing()
        alerts.extend(mix_alerts)
        logger.info(f"Detected {len(mix_alerts)} CoinJoin mixing candidate structures.")

        # 4. Detect Ransomware Payment Aggregations
        ransom_alerts = self._detect_ransomware_patterns()
        alerts.extend(ransom_alerts)
        logger.info(f"Detected {len(ransom_alerts)} ransomware aggregation candidate structures.")

        # Sort by confidence descending
        alerts.sort(key=lambda a: a.confidence, reverse=True)
        self.detected_alerts = alerts

        # Build txid -> typologies map
        self.tx_typology_map.clear()
        for a in alerts:
            for tid in a.member_txids:
                if a.predicted_pattern_type not in self.tx_typology_map[tid]:
                    self.tx_typology_map[tid].append(a.predicted_pattern_type)

        self.is_scanned = True
        logger.info(f"Typology detection completed! Total candidate alerts generated: {len(self.detected_alerts)}")

    @staticmethod
    def _timestamp(value: Any) -> datetime:
        """Normalize loader timestamps for ordering and time-window checks."""
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    def _detect_peeling_chains(self) -> List[AlertSummary]:
        """
        Detect one scenario-level linear peeling chain at most.

        A peel transaction has one or two inputs and either one V7 linear
        output or two asymmetric outputs. The carried output must be reused as
        an input by the next peel transaction in chronological order. The
        linear form is supported because the V7 generator emits the change
        path as a one-output hop.
        """
        alerts = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = sorted(
                [data_service.txid_map[t] for t in txids if t in data_service.txid_map],
                key=lambda t: self._timestamp(t["timestamp"]),
            )
            candidates = []
            for tx in txs:
                if len(tx["input_addresses"]) not in (1, 2) or len(tx["output_addresses"]) not in (1, 2):
                    continue
                amounts = tx.get("output_amounts", [])
                if len(amounts) not in (1, 2) or min(amounts) <= 0:
                    continue
                if len(amounts) == 2 and max(amounts) / min(amounts) < 2.0:
                    continue
                candidates.append(tx)

            if len(candidates) < 3:
                continue

            input_to_tx = {}
            for tx in candidates:
                for addr in tx["input_addresses"]:
                    input_to_tx.setdefault(addr, []).append(tx)

            best_chain = []
            for start_tx in candidates:
                chain = [start_tx]
                current = start_tx
                while True:
                    amounts = current["output_amounts"]
                    carry_addr = current["output_addresses"][amounts.index(max(amounts))]
                    next_candidates = [
                        tx for tx in input_to_tx.get(carry_addr, [])
                        if tx["txid"] not in {item["txid"] for item in chain}
                        and self._timestamp(tx["timestamp"]) > self._timestamp(current["timestamp"])
                        and (self._timestamp(tx["timestamp"]) - self._timestamp(current["timestamp"])).total_seconds() <= 6 * 3600
                        and max(tx["output_amounts"]) <= max(amounts) * 1.05
                    ]
                    if not next_candidates:
                        break
                    current = min(next_candidates, key=lambda t: self._timestamp(t["timestamp"]))
                    chain.append(current)
                if len(chain) > len(best_chain):
                    best_chain = chain

            if len(best_chain) < 5:
                continue
            if not all(
                max(best_chain[index + 1]["output_amounts"])
                < max(best_chain[index]["output_amounts"])
                for index in range(len(best_chain) - 1)
            ):
                continue
            chain = best_chain
            member_txids = [t["txid"] for t in chain]
            member_wallets = list({addr for t in chain for addr in t["input_addresses"] + t["output_addresses"]})
            has_suspicious_infra = any(
                t.get("node_type") in ["tor_exit_node", "vpn_proxy", "bulletproof_host"] for t in chain
            )
            conf = min(0.98, 0.70 + len(chain) * 0.05 + (0.10 if has_suspicious_infra else 0.0))
            alert = AlertSummary(
                candidate_id=f"cand_peel_{sc_id}_{chain[0]['txid']}",
                scenario_id=sc_id,
                predicted_pattern_type="peeling_chain",
                confidence=round(conf, 3),
                severity="CRITICAL" if conf >= 0.85 else "HIGH",
                explanation=(
                    f"Chronological asymmetric peeling chain with carry-address reuse across {len(chain)} hops. "
                    f"Origin infrastructure: {chain[0].get('node_type', 'unknown')} ({chain[0].get('asn', '')})."
                ),
                primary_wallet=chain[0]["input_addresses"][0],
                member_txids=member_txids,
                member_wallets=member_wallets[:10],
                detected_at=str(chain[0]["timestamp"]),
            )
            alerts.append(alert)
            self._cache_evidence(alert, chain, heuristic_type="peeling_chain")
        return alerts

    def _detect_layering(self) -> List[AlertSummary]:
        """
        Detect one scenario-level fan-out/fan-in layering candidate at most.
        Direct recipient overlap, chronological order, and a bounded time
        window are required; scenario size alone is not evidence of layering.
        """
        alerts = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = [data_service.txid_map[t] for t in txids if t in data_service.txid_map]
            
            # Find fan-out transactions (1-to-many)
            fan_outs = [t for t in txs if len(t["input_addresses"]) <= 2 and len(t["output_addresses"]) >= 3]
            # Find fan-in transactions (many-to-1)
            fan_ins = [t for t in txs if len(t["input_addresses"]) >= 3 and len(t["output_addresses"]) <= 2]
            
            scenario_alerted = False
            if fan_outs and fan_ins:
                for fo in fan_outs:
                    if scenario_alerted:
                        break
                    fo_outputs = set(fo["output_addresses"])
                    for fi in fan_ins:
                        fi_inputs = set(fi["input_addresses"])
                        overlap = fo_outputs.intersection(fi_inputs)
                        fo_time = self._timestamp(fo["timestamp"])
                        fi_time = self._timestamp(fi["timestamp"])
                        overlap_ratio = len(overlap) / len(fo_outputs) if fo_outputs else 0.0

                        if (
                            overlap
                            and overlap_ratio >= 0.60
                            and fi_time > fo_time
                            and (fi_time - fo_time).total_seconds() <= 72 * 3600
                        ):
                            member_txids = list({fo["txid"], fi["txid"]})
                            member_wallets = list(set(fo["input_addresses"] + fo["output_addresses"] + fi["input_addresses"] + fi["output_addresses"]))
                            primary_wallet = fo["input_addresses"][0]
                            
                            conf = 0.88
                            cand_id = f"cand_layer_{sc_id}_{fo['txid']}"
                            alert = AlertSummary(
                                candidate_id=cand_id,
                                scenario_id=sc_id,
                                predicted_pattern_type="layering",
                                confidence=round(conf, 3),
                                severity="HIGH",
                                explanation=(
                                    f"Layering structure: Fan-out from {len(fo['output_addresses'])} outputs followed by "
                                    f"fan-in reconvergence into consolidation wallet {fi['output_addresses'][0]}."
                                ),
                                primary_wallet=primary_wallet,
                                member_txids=member_txids,
                                member_wallets=member_wallets[:10],
                                detected_at=str(fo["timestamp"])
                            )
                            alerts.append(alert)
                            self._cache_evidence(alert, [fo, fi], heuristic_type="layering")
                            scenario_alerted = True
                            break
        return alerts

    def _detect_mixing(self) -> List[AlertSummary]:
        """
        Detect one scenario-level CoinJoin-like candidate at most.

        The candidate requires multi-party topology and a scale-independent
        near-equal output denomination test. Duplicate output values alone are
        not sufficient evidence.
        """
        alerts = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = [data_service.txid_map[t] for t in txids if t in data_service.txid_map]
            best_tx = None
            best_cv = None
            for tx in txs:
                num_in = len(tx["input_addresses"])
                num_out = len(tx["output_addresses"])
                if num_in < 3 or num_out < 3 or num_in != num_out:
                    continue
                out_amts = [float(value) for value in tx.get("output_amounts", [])]
                mean_amt = sum(out_amts) / len(out_amts) if out_amts else 0.0
                if mean_amt <= 0:
                    continue
                variance = sum((value - mean_amt) ** 2 for value in out_amts) / len(out_amts)
                cv = variance ** 0.5 / mean_amt
                if cv <= 0.10 and (best_cv is None or cv < best_cv):
                    best_tx = tx
                    best_cv = cv

            if best_tx is not None:
                tx = best_tx
                num_in = len(tx["input_addresses"])
                num_out = len(tx["output_addresses"])
                out_amts = [float(value) for value in tx["output_amounts"]]
                mean_amt = sum(out_amts) / len(out_amts)
                conf = 0.82
                cand_id = f"cand_mix_{sc_id}_{tx['txid']}"
                alert = AlertSummary(
                    candidate_id=cand_id,
                    scenario_id=sc_id,
                    predicted_pattern_type="mixing",
                    confidence=conf,
                    severity="HIGH",
                    explanation=(
                        f"CoinJoin-like multi-party transaction: {num_in} inputs -> {num_out} outputs "
                        f"with near-equal denominations (output CV {best_cv:.3f}, avg {mean_amt:.4f} BTC)."
                    ),
                    primary_wallet=tx["input_addresses"][0],
                    member_txids=[tx["txid"]],
                    member_wallets=list(set(tx["input_addresses"] + tx["output_addresses"]))[:10],
                    detected_at=str(tx["timestamp"])
                )
                alerts.append(alert)
                self._cache_evidence(alert, [tx], heuristic_type="mixing")
        return alerts

    def _detect_ransomware_patterns(self) -> List[AlertSummary]:
        """
        Detect one scenario-level suspicious payment aggregation at most.

        Infrastructure is supporting evidence only. A candidate also needs a
        shared transaction flow and fan-in/aggregation structure in the data.
        """
        alerts = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = sorted(
                [data_service.txid_map[t] for t in txids if t in data_service.txid_map],
                key=lambda t: self._timestamp(t["timestamp"]),
            )
            if len(txs) > 50:
                continue

            threat_txs = [
                t for t in txs
                if t.get("node_type") in ["bulletproof_host", "tor_exit_node", "vpn_proxy"]
            ]
            if len(threat_txs) < 2 or len(txs) < 3:
                continue

            # Ransomware payment aggregation in this dataset is a short,
            # high-risk flow with a genuine two-party consolidation step. A
            # generic shared address or suspicious relay alone is not enough.
            fan_in_txs = [
                t for t in txs
                if len(t.get("input_addresses", [])) == 2
                and len(t.get("output_addresses", [])) <= 2
            ]
            has_aggregation_flow = any(
                bool(set(fan_in.get("output_addresses", [])) & set(later.get("input_addresses", [])))
                and self._timestamp(later["timestamp"]) > self._timestamp(fan_in["timestamp"])
                for fan_in in fan_in_txs
                for later in txs
            )
            has_fan_out = any(len(t.get("output_addresses", [])) >= 3 for t in txs)
            suspicious_ratio = len(threat_txs) / len(txs)
            if (
                not fan_in_txs
                or not has_aggregation_flow
                or has_fan_out
                or suspicious_ratio < 0.25
            ):
                continue

            tx0 = threat_txs[0]
            member_txids = [t["txid"] for t in txs]
            member_wallets = list({
                addr for t in txs for addr in t.get("input_addresses", []) + t.get("output_addresses", [])
            })
            conf = min(0.92, 0.72 + 0.04 * len(threat_txs))
            alert = AlertSummary(
                candidate_id=f"cand_ransom_{sc_id}_{tx0['txid']}",
                scenario_id=sc_id,
                predicted_pattern_type="ransomware",
                confidence=round(conf, 3),
                severity="HIGH",
                explanation=(
                    f"Suspicious payment aggregation: {len(threat_txs)} high-risk relay transactions "
                    f"participate in a short shared flow with two-party fan-in evidence ({tx0.get('relay_ip', '')}, "
                    f"{tx0.get('asn', '')})."
                ),
                primary_wallet=tx0["input_addresses"][0],
                member_txids=member_txids[:50],
                member_wallets=member_wallets[:10],
                detected_at=str(tx0["timestamp"])
            )
            alerts.append(alert)
            self._cache_evidence(alert, txs[: min(len(txs), 10)], heuristic_type="ransomware")
        return alerts

    def _cache_evidence(self, alert: AlertSummary, transactions: List[Dict[str, Any]], heuristic_type: str):
        """Cache heuristic evidence and optional model-derived attribution."""
        tx_records = []
        for tx in transactions:
            tx_records.append({
                "txid": tx["txid"],
                "timestamp": str(tx["timestamp"]),
                "relay_timestamp": str(tx.get("relay_timestamp", tx["timestamp"])),
                "input_addresses": tx["input_addresses"],
                "output_addresses": tx["output_addresses"],
                "input_amounts": tx["input_amounts"],
                "output_amounts": tx["output_amounts"],
                "fee_btc": float(tx["fee_btc"]),
                "script_type": str(tx["script_type"]),
                "relay_ip": str(tx.get("relay_ip", "")),
                "relay_port": int(tx.get("relay_port", 8333)),
                "node_type": str(tx.get("node_type", "")),
                "country_code": str(tx.get("country_code", "")),
                "asn": str(tx.get("asn", "")),
                "user_agent": str(tx.get("user_agent", "/Satoshi:22.0.0/")),
                "propagation_delta_ms": float(tx.get("propagation_delta_ms", 0.0))
            })

        infra_types = [t.get("node_type", "residential") for t in tx_records]
        infra_dist = {k: infra_types.count(k) for k in set(infra_types)}
        
        evidence = EvidenceResponse(
            candidate_id=alert.candidate_id,
            scenario_id=alert.scenario_id,
            predicted_pattern_type=alert.predicted_pattern_type,
            confidence=alert.confidence,
            typology_heuristic_match={
                "heuristic_name": f"{heuristic_type}_traversal",
                "chain_length": len(alert.member_txids),
                "reconvergence_detected": heuristic_type == "layering",
                "primary_destination": alert.primary_wallet
            },
            # Populated on demand by get_evidence(). Keeping detector startup
            # heuristic-only avoids running one XGBoost explanation per alert.
            ml_feature_attributions=[],
            telemetry_summary={
                "origin_ips": list({t["relay_ip"] for t in tx_records if t["relay_ip"]}),
                "origin_asns": list({t["asn"] for t in tx_records if t["asn"]}),
                "countries": list({t["country_code"] for t in tx_records if t["country_code"]}),
                "infrastructure_distribution": infra_dist
            },
            transactions=tx_records
        )
        self.evidence_cache[alert.candidate_id] = evidence

    def get_alerts(
        self,
        min_confidence: float = 0.50,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[AlertSummary]:
        if not self.is_scanned:
            self.scan_all_typologies()
            
        filtered = [
            a for a in self.detected_alerts
            if a.confidence >= min_confidence
            and (pattern_type is None or a.predicted_pattern_type.lower() == pattern_type.lower())
        ]
        return filtered[:limit]

    def get_evidence(self, candidate_id: str) -> Optional[EvidenceResponse]:
        if not self.is_scanned:
            self.scan_all_typologies()
        evidence = self.evidence_cache.get(candidate_id)
        if evidence is None or candidate_id in self._attribution_attempted:
            return evidence

        self._attribution_attempted.add(candidate_id)
        try:
            from backend.app.services.ml_service import ml_service

            evidence.ml_feature_attributions = [
                FeatureAttribution(**item)
                for item in ml_service.explain_features(evidence.transactions)
            ]
        except Exception:
            # Heuristic evidence remains useful when optional ML attribution
            # cannot be produced, but no fabricated SHAP values are returned.
            logger.exception("Could not compute ML feature attribution for %s", candidate_id)
        return evidence

    def get_typologies_for_tx(self, txid: int) -> List[str]:
        """Returns all detected typology patterns associated with a specific transaction."""
        if not self.is_scanned:
            self.scan_all_typologies()
        return self.tx_typology_map.get(int(txid), [])

# Global Singleton Instance
typology_detector = TypologyDetector()
