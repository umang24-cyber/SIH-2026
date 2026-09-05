"""
Algorithmic Typology Detection Engine for Bitcoin Forensic Graph Analytics.

DESIGN (post Task-2 fix):
  This module is responsible ONLY for structural candidate discovery.
  It identifies subgraphs that match rough topological shapes (peeling chain
  sequences, fan-out/fan-in overlap, near-equal-output clusters, suspicious
  payment aggregations).

  For each candidate it calls ml_service.score_candidate() which returns:
    - binary is_illicit probability (binary XGBoost model)
    - typology class or explicit ambiguity + calibrated typology confidence
    - SHAP attributions for BOTH models
    - natural-language typology explanation from actual SHAP features

  The final alert shown on the dashboard uses:
    - typology label  = ML model class or explicit low-confidence ambiguity
                         (NOT the detector's shape guess)
    - binary_confidence = binary model probability for the illicit prediction
    - typology_confidence = ML model's calibrated typology probability
    - explanation     = ML model SHAP-derived natural-language string
    - is_ml_driven    = True (always, for every alert this module emits)

  Hardcoded confidence constants (conf = 0.88, etc.) have been completely
  removed from this module.  If the ML model returns is_illicit=False for a
  structural candidate, that candidate is DROPPED rather than forced into an
  alert with a made-up confidence score.

Implements structural heuristics for:
  1. Peeling Chains  (1→2 out asymmetric carry-address traversal)
  2. Layering        (Fan-out → Fan-in reconvergence)
  3. CoinJoin Mixing (N→N equal-denomination anonymization)
  4. Ransomware      (Short suspicious-infrastructure payment aggregation)
"""
import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from collections import Counter, defaultdict
from backend.app.models.schemas import AlertSummary, FeatureAttribution, EvidenceResponse
from backend.app.services.data_service import data_service

logger = logging.getLogger(__name__)


def _severity_from_confidence(conf: float) -> str:
    if conf >= 0.85:
        return "CRITICAL"
    if conf >= 0.70:
        return "HIGH"
    if conf >= 0.55:
        return "MEDIUM"
    return "LOW"


class TypologyDetector:
    def __init__(self):
        self.detected_alerts: List[AlertSummary] = []
        self.evidence_cache: Dict[str, EvidenceResponse] = {}
        self._attribution_attempted: Set[str] = set()
        self.tx_typology_map: Dict[int, List[str]] = defaultdict(list)
        self.is_scanned: bool = False

    def scan_all_typologies(self):
        """
        Run structural candidate detectors, then score every candidate with the
        ML models.  Only candidates where binary model predicts is_illicit=True
        emit alerts.  All labels and confidence values come from the ML models.
        """
        if not data_service.is_ready:
            data_service.initialize()

        # Import here to avoid circular imports at module load
        from backend.app.services.ml_service import ml_service

        logger.info("Running structural candidate discovery across all scenarios...")
        self.evidence_cache.clear()
        self._attribution_attempted.clear()
        alerts = []

        # 1. Discover Peeling Chain candidates
        peel_candidates = self._discover_peeling_chain_candidates()
        logger.info(f"Discovered {len(peel_candidates)} peeling chain structural candidates.")

        # 2. Discover Layering candidates
        layer_candidates = self._discover_layering_candidates()
        logger.info(f"Discovered {len(layer_candidates)} layering structural candidates.")

        # 3. Discover Mixing / CoinJoin candidates
        mix_candidates = self._discover_mixing_candidates()
        logger.info(f"Discovered {len(mix_candidates)} mixing structural candidates.")

        # 4. Discover Ransomware payment aggregation candidates
        ransom_candidates = self._discover_ransomware_candidates()
        logger.info(f"Discovered {len(ransom_candidates)} ransomware structural candidates.")

        all_candidates = peel_candidates + layer_candidates + mix_candidates + ransom_candidates

        # 5. Score every candidate with the ML models
        logger.info(f"Scoring {len(all_candidates)} total candidates with ML models...")
        ml_alerts_count = 0
        dropped_count = 0

        for cand in all_candidates:
            tx_records = cand["tx_records"]
            cand_id = cand["candidate_id"]

            try:
                ml_result = ml_service.score_candidate(tx_records, candidate_id=cand_id)
            except Exception:
                logger.exception("ML scoring failed for candidate %s — skipping.", cand_id)
                dropped_count += 1
                continue

            if not ml_result.get("is_illicit", False):
                # Structural shape matched, but ML says licit — do not emit an alert.
                dropped_count += 1
                continue

            # ML model drives all final alert fields
            ml_typology    = ml_result["typology"]
            ml_binary_confidence = ml_result["binary_confidence"]
            ml_typology_confidence = ml_result["typology_confidence"]
            ml_risk_score  = ml_result["risk_score"]
            ml_explanation = ml_result.get("typology_explanation", "")
            binary_shap    = ml_result.get("binary_shap", [])
            typology_shap  = ml_result.get("typology_shap", [])

            # Preserve the existing severity semantics: severity reflects
            # confidence in the named typology, not binary illicit risk.
            severity = _severity_from_confidence(ml_typology_confidence)

            alert = AlertSummary(
                candidate_id=cand_id,
                scenario_id=cand["scenario_id"],
                predicted_pattern_type=ml_typology,
                binary_confidence=round(ml_binary_confidence, 4),
                typology_confidence=round(ml_typology_confidence, 4),
                severity=severity,
                explanation=ml_explanation,
                primary_wallet=cand["primary_wallet"],
                member_txids=cand["member_txids"],
                member_wallets=cand["member_wallets"][:10],
                detected_at=cand["detected_at"],
                is_ml_driven=True,
                risk_score=round(ml_risk_score, 4),
            )
            alerts.append(alert)
            ml_alerts_count += 1

            # Cache evidence immediately with SHAP already computed
            self._cache_evidence(
                alert=alert,
                transactions=tx_records,
                heuristic_type=cand["structural_type"],
                binary_shap=binary_shap,
                typology_shap=typology_shap,
                typology_explanation=ml_explanation,
            )

        # Sort by typology confidence, preserving the previous alert ordering.
        alerts.sort(key=lambda a: a.typology_confidence, reverse=True)
        self.detected_alerts = alerts

        # Build txid → typologies map
        self.tx_typology_map.clear()
        for a in alerts:
            for tid in a.member_txids:
                if a.predicted_pattern_type not in self.tx_typology_map[tid]:
                    self.tx_typology_map[tid].append(a.predicted_pattern_type)

        self.is_scanned = True
        logger.info(
            "Typology detection complete. ML-driven alerts: %d. Dropped (not illicit per ML): %d.",
            ml_alerts_count,
            dropped_count,
        )

    # ------------------------------------------------------------------
    # Static helper
    # ------------------------------------------------------------------

    @staticmethod
    def _timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    # ------------------------------------------------------------------
    # Structural candidate discovery — NO label assignment, NO confidence
    # ------------------------------------------------------------------

    def _discover_peeling_chain_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify scenarios that contain a chronological asymmetric carry-address
        chain with at least 5 hops.  Returns candidate dicts, NOT alert objects.
        """
        candidates = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = sorted(
                [data_service.txid_map[t] for t in txids if t in data_service.txid_map],
                key=lambda t: self._timestamp(t["timestamp"]),
            )
            shape_candidates = []
            for tx in txs:
                if len(tx["input_addresses"]) not in (1, 2) or len(tx["output_addresses"]) not in (1, 2):
                    continue
                amounts = tx.get("output_amounts", [])
                if len(amounts) not in (1, 2) or min(amounts) <= 0:
                    continue
                if len(amounts) == 2 and max(amounts) / min(amounts) < 2.0:
                    continue
                shape_candidates.append(tx)

            if len(shape_candidates) < 3:
                continue

            input_to_tx = {}
            for tx in shape_candidates:
                for addr in tx["input_addresses"]:
                    input_to_tx.setdefault(addr, []).append(tx)

            best_chain = []
            for start_tx in shape_candidates:
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
                max(best_chain[i + 1]["output_amounts"]) < max(best_chain[i]["output_amounts"])
                for i in range(len(best_chain) - 1)
            ):
                continue

            chain = best_chain
            member_txids = [t["txid"] for t in chain]
            member_wallets = list({addr for t in chain for addr in t["input_addresses"] + t["output_addresses"]})

            candidates.append({
                "candidate_id": f"cand_peel_{sc_id}_{chain[0]['txid']}",
                "scenario_id": sc_id,
                "structural_type": "peeling_chain",
                "primary_wallet": chain[0]["input_addresses"][0],
                "member_txids": member_txids,
                "member_wallets": member_wallets,
                "detected_at": str(chain[0]["timestamp"]),
                "tx_records": chain,
            })
        return candidates

    def _discover_layering_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify fan-out → fan-in reconvergence structures with ≥60% address overlap,
        chronologically ordered within 72 hours.
        """
        candidates = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = [data_service.txid_map[t] for t in txids if t in data_service.txid_map]
            fan_outs = [t for t in txs if len(t["input_addresses"]) <= 2 and len(t["output_addresses"]) >= 3]
            fan_ins  = [t for t in txs if len(t["input_addresses"]) >= 3 and len(t["output_addresses"]) <= 2]

            scenario_found = False
            if fan_outs and fan_ins:
                for fo in fan_outs:
                    if scenario_found:
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
                            member_wallets = list(set(
                                fo["input_addresses"] + fo["output_addresses"] +
                                fi["input_addresses"] + fi["output_addresses"]
                            ))
                            candidates.append({
                                "candidate_id": f"cand_layer_{sc_id}_{fo['txid']}",
                                "scenario_id": sc_id,
                                "structural_type": "layering",
                                "primary_wallet": fo["input_addresses"][0],
                                "member_txids": member_txids,
                                "member_wallets": member_wallets,
                                "detected_at": str(fo["timestamp"]),
                                "tx_records": [fo, fi],
                            })
                            scenario_found = True
                            break
        return candidates

    def _discover_mixing_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify transactions with N≥3 equal-count inputs and outputs whose output
        amounts have coefficient-of-variation ≤ 0.10 (near-equal denominations).
        """
        candidates = []
        for sc_id, txids in data_service.scenario_tx_map.items():
            txs = [data_service.txid_map[t] for t in txids if t in data_service.txid_map]
            best_tx = None
            best_cv = None
            for tx in txs:
                num_in  = len(tx["input_addresses"])
                num_out = len(tx["output_addresses"])
                if num_in < 3 or num_out < 3 or num_in != num_out:
                    continue
                out_amts = [float(v) for v in tx.get("output_amounts", [])]
                mean_amt = sum(out_amts) / len(out_amts) if out_amts else 0.0
                if mean_amt <= 0:
                    continue
                variance = sum((v - mean_amt) ** 2 for v in out_amts) / len(out_amts)
                cv = variance ** 0.5 / mean_amt
                if cv <= 0.10 and (best_cv is None or cv < best_cv):
                    best_tx = tx
                    best_cv = cv

            if best_tx is not None:
                tx = best_tx
                candidates.append({
                    "candidate_id": f"cand_mix_{sc_id}_{tx['txid']}",
                    "scenario_id": sc_id,
                    "structural_type": "mixing",
                    "primary_wallet": tx["input_addresses"][0],
                    "member_txids": [tx["txid"]],
                    "member_wallets": list(set(tx["input_addresses"] + tx["output_addresses"])),
                    "detected_at": str(tx["timestamp"]),
                    "tx_records": [tx],
                })
        return candidates

    def _discover_ransomware_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify short scenarios (≤50 txns) with ≥2 high-risk relay transactions,
        a genuine two-party fan-in consolidation step, and no fan-out.
        """
        candidates = []
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

            if not fan_in_txs or not has_aggregation_flow or has_fan_out or suspicious_ratio < 0.25:
                continue

            tx0 = threat_txs[0]
            member_txids = [t["txid"] for t in txs]
            member_wallets = list({
                addr for t in txs for addr in t.get("input_addresses", []) + t.get("output_addresses", [])
            })
            candidates.append({
                "candidate_id": f"cand_ransom_{sc_id}_{tx0['txid']}",
                "scenario_id": sc_id,
                "structural_type": "ransomware",
                "primary_wallet": tx0["input_addresses"][0],
                "member_txids": member_txids[:50],
                "member_wallets": member_wallets,
                "detected_at": str(tx0["timestamp"]),
                "tx_records": txs[:min(len(txs), 10)],
            })
        return candidates

    # ------------------------------------------------------------------
    # Evidence caching — now populated at scan time with pre-computed SHAP
    # ------------------------------------------------------------------

    def _cache_evidence(
        self,
        alert: AlertSummary,
        transactions: List[Dict[str, Any]],
        heuristic_type: str,
        binary_shap: List[Dict[str, Any]],
        typology_shap: List[Dict[str, Any]],
        typology_explanation: str,
    ):
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
                "propagation_delta_ms": float(tx.get("propagation_delta_ms", 0.0)),
            })

        infra_types = [t.get("node_type", "residential") for t in tx_records]
        infra_dist  = {k: infra_types.count(k) for k in set(infra_types)}

        evidence = EvidenceResponse(
            candidate_id=alert.candidate_id,
            scenario_id=alert.scenario_id,
            predicted_pattern_type=alert.predicted_pattern_type,
            binary_confidence=alert.binary_confidence,
            typology_confidence=alert.typology_confidence,
            typology_heuristic_match={
                "heuristic_name": f"{heuristic_type}_traversal",
                "chain_length": len(alert.member_txids),
                "reconvergence_detected": heuristic_type == "layering",
                "primary_destination": alert.primary_wallet,
            },
            # Binary SHAP from the ML model (pre-computed at scan time)
            ml_feature_attributions=[
                FeatureAttribution(**item) for item in binary_shap
            ],
            # Typology SHAP from the ML model (pre-computed at scan time)
            typology_shap_attributions=[
                FeatureAttribution(**item) for item in typology_shap
            ],
            typology_explanation=typology_explanation,
            telemetry_summary={
                "origin_ips":  list({t["relay_ip"]  for t in tx_records if t["relay_ip"]}),
                "origin_asns": list({t["asn"]        for t in tx_records if t["asn"]}),
                "countries":   list({t["country_code"] for t in tx_records if t["country_code"]}),
                "infrastructure_distribution": infra_dist,
            },
            transactions=tx_records,
        )
        self.evidence_cache[alert.candidate_id] = evidence

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_alerts(
        self,
        min_confidence: float = 0.50,
        pattern_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[AlertSummary]:
        if not self.is_scanned:
            self.scan_all_typologies()
        filtered = [
            a for a in self.detected_alerts
            if a.typology_confidence >= min_confidence
            and (pattern_type is None or a.predicted_pattern_type.lower() == pattern_type.lower())
        ]
        return filtered[:limit]

    def get_evidence(self, candidate_id: str) -> Optional[EvidenceResponse]:
        """
        Return cached evidence.  Binary and typology SHAP are pre-computed at
        scan time and are always present — no lazy re-invocation needed.
        """
        if not self.is_scanned:
            self.scan_all_typologies()
        return self.evidence_cache.get(candidate_id)

    def get_typologies_for_tx(self, txid: int) -> List[str]:
        if not self.is_scanned:
            self.scan_all_typologies()
        return self.tx_typology_map.get(int(txid), [])


# Global Singleton Instance
typology_detector = TypologyDetector()
