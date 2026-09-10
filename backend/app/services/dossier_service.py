"""System-generated forensic investigation summary and recommendation report."""
import time
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.ml_service import ml_service
from backend.app.services.taint_service import taint_service
from backend.app.services.db_service import db_service

logger = logging.getLogger(__name__)

class DossierService:
    def generate_dossier(self, txid: int) -> Dict[str, Any]:
        """Generates a structured system-generated investigation summary."""
        tx = data_service.txid_map.get(txid)
        if not tx:
            # Try to retrieve from SQLite if already saved
            saved = db_service.get_dossier(str(txid))
            if saved:
                return saved
            return {"error": f"Transaction {txid} not found", "txid": txid}

        node_type = str(tx.get("node_type", "residential"))
        is_tor = node_type == "tor_exit_node" or bool(tx.get("is_tor", False))
        input_addresses = tx.get("input_addresses", [])
        output_addresses = tx.get("output_addresses", [])
        btc_value = float(sum(tx.get("output_amounts", [0.0])))
        timestamp_str = str(tx.get("timestamp", ""))
        delta_t_sec = float(tx.get("propagation_delta_ms", 0.0)) / 1000.0

        # Cluster and entity attribution
        entity_id = "UNKNOWN"
        cluster_wallets: List[str] = []
        if input_addresses:
            first_addr = input_addresses[0]
            entity_id = clustering_service.get_entity_id(first_addr)
            cluster_wallets = clustering_service.get_cluster_wallets(first_addr)

        # ML and typology analysis
        ml_pred = ml_service.predict_risk(txid)
        risk_score = ml_pred.get("risk_score", 0.0)
        typologies_detected = typology_detector.get_typologies_for_tx(txid)

        # Taint hop summary
        taint_summary = []
        if input_addresses:
            taint_result = taint_service.propagate_taint(input_addresses[0], max_depth=3)
            taint_summary = taint_result.contaminated_wallets[:5]

        # System-generated recommendations. They are not legal instruments.
        case_id = f"CASE-2026-TX{txid}"
        
        recommended_actions = [
            f"1. Consider requesting records from recipient VASPs/exchanges holding these observed output addresses: {', '.join(output_addresses[:3])}. Any request requires authorized investigator and legal review.",
            f"2. Consider preserving relevant KYC, bank-linkage, and recorded relay-telemetry records for entity cluster {entity_id} ({len(cluster_wallets)} observed linked addresses), subject to applicable process and review.",
            "3. Consider referral to the appropriate financial-intelligence authority for review under applicable reporting requirements; verify current requirements before action."
        ]
        if is_tor:
            recommended_actions.append(
                f"4. Consider coordination with relevant international channels regarding the observed relay telemetry {tx.get('relay_ip', 'UNKNOWN')} ({tx.get('country_code', 'UNKNOWN')}); this report does not establish identity or attribution."
            )

        dossier_res = {
            "case_metadata": {
                "dossier_id": case_id,
                "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "document_owner": "BitKaun Forensic Engine (v8.0.0)",
                "target_entity": f"TX:{txid}",
                "legal_context": "This system issues no legal instrument. Applicable authorities and procedures require authorized investigator and legal review.",
                "document_status": "System-generated recommendations — require authorized investigator/legal review.",
                "data_status": "Dual-Stream Ledger & Network Telemetry (v8.0 Production)",
                "model_status": "V8.0 Production AML ML Benchmark",
                "case_status": "CONFIDENTIAL // LAW ENFORCEMENT SUMMARY",
                "engine_version": "v8.0.0"
            },
            "transaction_evidence": {
                "txid": txid,
                "timestamp_utc": timestamp_str,
                "transferred_btc": round(btc_value, 4),
                "fee_btc": float(tx.get("fee_btc", 0.0001)),
                "input_addresses": input_addresses,
                "output_addresses": output_addresses
            },
            "network_telemetry_observation": {
                "observed_relay_ip": str(tx.get("relay_ip", "UNKNOWN")),
                "recorded_country_code": str(tx.get("country_code", "UNKNOWN")),
                "recorded_asn": str(tx.get("asn", "UNKNOWN")),
                "recorded_isp": str(tx.get("isp", "UNKNOWN")),
                "recorded_node_type": node_type,
                "tor_exit_indicator": is_tor,
                "propagation_delta_t_seconds": round(delta_t_sec, 3)
            },
            "entity_clustering": {
                "entity_cluster_id": entity_id,
                "total_cioh_linked_addresses_observed": len(cluster_wallets),
                "sample_co_owned_addresses": cluster_wallets[:10]
            },
            "threat_assessment": {
                "composite_risk_score": risk_score,
                "risk_rating": "CRITICAL" if risk_score >= 0.75 else ("HIGH" if risk_score >= 0.50 else "MODERATE"),
                "detected_typologies": typologies_detected,
                "taint_hop_flows_count": len(taint_summary)
            },
            "recommended_investigative_actions": recommended_actions
        }

        # Auto-save dossier to SQLite
        try:
            db_service.save_dossier(dossier_res)
        except Exception as exc:
            logger.warning(f"Could not persist dossier {case_id} to SQLite: {exc}")

        # Auto-save proper forensic file copies to local REPORTS_DIR
        self._save_to_reports(case_id, dossier_res)

        return dossier_res

    def _save_to_reports(self, case_id: str, dossier: Dict[str, Any], html_content: Optional[str] = None) -> None:
        """
        Safely and atomically persists JSON, TXT, and optional HTML forensic reports
        to REPORTS_DIR for offline LEA / NTRO review. Sanitizes filenames against OS restrictions.
        """
        import re
        import json
        from backend.app.core.config import REPORTS_DIR

        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', str(case_id).strip())
            if not safe_name:
                safe_name = f"CASE_REPORT_{int(time.time())}"

            # 1. Atomic save of structured JSON dossier
            json_file = REPORTS_DIR / f"{safe_name}.json"
            tmp_json = REPORTS_DIR / f"{safe_name}.json.tmp"
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(dossier, f, indent=2, ensure_ascii=False)
                f.flush()
            tmp_json.replace(json_file)

            # 2. Atomic save of clean ASCII TXT dossier
            txt_file = REPORTS_DIR / f"{safe_name}.txt"
            tmp_txt = REPORTS_DIR / f"{safe_name}.txt.tmp"
            meta = dossier.get("case_metadata", {})
            tx_ev = dossier.get("transaction_evidence", {})
            net = dossier.get("network_telemetry_observation", {})
            ent = dossier.get("entity_clustering", {})
            threat = dossier.get("threat_assessment", {})
            recs = dossier.get("recommended_investigative_actions", [])

            txt_lines = [
                "=" * 80,
                "           BITKAUN V8.0 FORENSIC INVESTIGATION SUMMARY (CONFIDENTIAL)",
                "=" * 80,
                f"DOSSIER ID          : {meta.get('dossier_id', safe_name)}",
                f"TARGET TRANSACTION  : {meta.get('target_entity', '')}",
                f"GENERATION TIMESTAMP: {meta.get('generation_timestamp', '')}",
                f"ENGINE VERSION      : {meta.get('engine_version', 'v8.0.0')}",
                f"COMPOSITE RISK SCORE: {threat.get('composite_risk_score', 0.0)} ({threat.get('risk_rating', 'UNKNOWN')})",
                f"DETECTED TYPOLOGIES : {', '.join(threat.get('detected_typologies', [])) or 'None Detected (Baseline Flow)'}",
                f"DATA STATUS         : {meta.get('data_status', 'Dual-Stream Ledger & Telemetry')}",
                f"MODEL STATUS        : {meta.get('model_status', 'V8.0 Production Benchmark')}",
                "-" * 80,
                "TRANSACTION EVIDENCE:",
                f"  - Timestamp UTC   : {tx_ev.get('timestamp_utc')}",
                f"  - Transferred BTC : {tx_ev.get('transferred_btc')} BTC",
                f"  - Fee BTC         : {tx_ev.get('fee_btc')} BTC",
                f"  - Input Wallets   : {', '.join(tx_ev.get('input_addresses', []))}",
                f"  - Output Wallets  : {', '.join(tx_ev.get('output_addresses', []))}",
                "-" * 80,
                "NETWORK TELEMETRY OBSERVATION:",
                f"  - Observed Relay IP  : {net.get('observed_relay_ip')} ({net.get('recorded_country_code')})",
                f"  - Autonomous System  : {net.get('recorded_asn')} - {net.get('recorded_isp')}",
                f"  - Relay Node Type    : {net.get('recorded_node_type')} (Tor Exit: {net.get('tor_exit_indicator')})",
                f"  - Propagation Delay  : {net.get('propagation_delta_t_seconds')} s",
                "-" * 80,
                "CIOH ENTITY CLUSTERING:",
                f"  - Cluster ID         : {ent.get('entity_cluster_id')}",
                f"  - Linked Addresses   : {ent.get('total_cioh_linked_addresses_observed')} co-owned addresses",
                "-" * 80,
                "RECOMMENDED INVESTIGATIVE ACTIONS:",
            ]
            for act in recs:
                txt_lines.append(f"  * {act}")
            txt_lines.append("=" * 80)

            with open(tmp_txt, "w", encoding="utf-8") as f:
                f.write("\n".join(txt_lines))
                f.flush()
            tmp_txt.replace(txt_file)

            # 3. Atomic save of HTML dossier if provided
            if html_content:
                html_file = REPORTS_DIR / f"{safe_name}.html"
                tmp_html = REPORTS_DIR / f"{safe_name}.html.tmp"
                with open(tmp_html, "w", encoding="utf-8") as f:
                    f.write(html_content)
                    f.flush()
                tmp_html.replace(html_file)

            logger.info(f"Safely persisted forensic dossier files to: {REPORTS_DIR / safe_name}.[json|txt|html]")
        except Exception as exc:
            logger.warning(f"Failed to safely persist dossier to REPORTS_DIR: {exc}")

    def generate_html_dossier(self, txid: int) -> str:
        """Generates a print-ready HTML investigation summary."""
        dossier = self.generate_dossier(txid)
        if "error" in dossier:
            return f"<html><body><h1>Error: {dossier['error']}</h1></body></html>"

        meta = dossier["case_metadata"]
        tx_ev = dossier["transaction_evidence"]
        net = dossier["network_telemetry_observation"]
        ent = dossier["entity_clustering"]
        threat = dossier["threat_assessment"]
        recommended_actions = dossier["recommended_investigative_actions"]

        recommendations_html = "".join([f"<li><strong>{d}</strong></li>" for d in recommended_actions])
        typologies_str = ", ".join(threat["detected_typologies"]) if threat["detected_typologies"] else "None Detected (Baseline Flow)"
        inputs_html = "<br>".join([f"<code>{a}</code>" for a in tx_ev["input_addresses"][:5]])
        outputs_html = "<br>".join([f"<code>{a}</code>" for a in tx_ev["output_addresses"][:5]])

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CONFIDENTIAL INVESTIGATIVE SUMMARY - {meta['dossier_id']}</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1e293b; background: #fff; line-height: 1.5; }}
    .header {{ border-bottom: 3px solid #0f172a; padding-bottom: 12px; margin-bottom: 25px; }}
    .confidential-badge {{ background: #dc2626; color: white; padding: 4px 12px; font-weight: bold; font-size: 13px; border-radius: 3px; display: inline-block; letter-spacing: 1px; }}
    h1 {{ font-size: 22px; color: #0f172a; margin: 10px 0 4px 0; }}
    .meta-table, .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    .meta-table td {{ padding: 6px; font-size: 13px; }}
    .data-table th {{ background: #f1f5f9; text-align: left; padding: 8px; font-size: 13px; border: 1px solid #cbd5e1; }}
    .data-table td {{ padding: 8px; font-size: 13px; border: 1px solid #cbd5e1; }}
    .section-title {{ font-size: 16px; font-weight: bold; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; margin-top: 25px; margin-bottom: 12px; }}
    .risk-badge-crit {{ background: #fee2e2; color: #991b1b; padding: 4px 8px; font-weight: bold; border-radius: 4px; border: 1px solid #f87171; }}
    .recommendations-box {{ background: #f8fafc; border-left: 4px solid #2563eb; padding: 15px; margin-top: 15px; }}
    .recommendations-box li {{ margin-bottom: 8px; font-size: 13px; }}
    code {{ background: #f1f5f9; padding: 2px 5px; font-family: Consolas, monospace; font-size: 12px; }}
    @media print {{
        body {{ margin: 20px; }}
        .no-print {{ display: none; }}
    }}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom: 20px; text-align: right;">
    <button onclick="window.print()" style="background: #0f172a; color: white; border: none; padding: 8px 16px; font-weight: bold; cursor: pointer; border-radius: 4px;">🖨️ Print / Save as PDF</button>
</div>

<div class="header">
    <div class="confidential-badge">CONFIDENTIAL // LAW ENFORCEMENT SUMMARY</div>
    <h1>FORENSIC INVESTIGATIVE SUMMARY</h1>
    <p style="font-size: 13px; color: #64748b; margin: 0;">Generated by BitKaun Forensic Engine (v8.0.0 Production) · Air-Gapped AML Analysis</p>
    <p style="font-size: 12px; color: #64748b; margin: 4px 0 0 0;">DATA STATUS: Dual-Stream Ledger & Network Telemetry · MODEL STATUS: V8.0 Production AML ML Benchmark</p>
</div>

<table class="meta-table">
    <tr>
        <td><strong>Case Reference ID:</strong></td>
        <td><code>{meta['dossier_id']}</code></td>
        <td><strong>Generated At:</strong></td>
        <td>{meta['generation_timestamp']}</td>
    </tr>
    <tr>
        <td><strong>Investigating Unit:</strong></td>
        <td>{meta['document_owner']}</td>
        <td><strong>Threat Rating:</strong></td>
        <td><span class="risk-badge-crit">{threat['risk_rating']} (Score: {threat['composite_risk_score']})</span></td>
    </tr>
</table>

<div class="section-title">1. TRANSACTION EVIDENTIARY RECORD</div>
<table class="data-table">
    <tr>
        <th style="width: 30%;">Transaction Hash (TXID)</th>
        <td><code>{tx_ev['txid']}</code></td>
    </tr>
    <tr>
        <th>Ledger Timestamp</th>
        <td>{tx_ev['timestamp_utc']}</td>
    </tr>
    <tr>
        <th>Transferred Value</th>
        <td><strong>{tx_ev['transferred_btc']:.4f} BTC</strong></td>
    </tr>
    <tr>
        <th>Input Wallets ({len(tx_ev['input_addresses'])})</th>
        <td>{inputs_html}</td>
    </tr>
    <tr>
        <th>Output Wallets ({len(tx_ev['output_addresses'])})</th>
        <td>{outputs_html}</td>
    </tr>
</table>

<div class="section-title">2. RECORDED NETWORK TELEMETRY</div>
<table class="data-table">
    <tr>
        <th style="width: 30%;">Observed Relay IP</th>
        <td><code>{net['observed_relay_ip']}</code></td>
    </tr>
    <tr>
        <th>ISP & Autonomous System</th>
        <td>{net['recorded_isp']} (ASN: {net['recorded_asn']})</td>
    </tr>
    <tr>
        <th>Recorded Country Code</th>
        <td>{net['recorded_country_code']}</td>
    </tr>
    <tr>
        <th>Recorded Infrastructure Indicator</th>
        <td><strong>{'Tor-exit indicator recorded' if net['tor_exit_indicator'] else 'No Tor-exit indicator recorded'}</strong></td>
    </tr>
    <tr>
        <th>Propagation Timing Delta (Δt)</th>
        <td>{net['propagation_delta_t_seconds']:.2f} seconds</td>
    </tr>
</table>

<div class="section-title">3. ENTITY CLUSTER ANALYSIS (CIOH)</div>
<table class="data-table">
    <tr>
        <th style="width: 30%;">Entity Cluster ID</th>
        <td><code>{ent['entity_cluster_id']}</code></td>
    </tr>
    <tr>
        <th>CIOH-linked addresses observed</th>
        <td><strong>{ent['total_cioh_linked_addresses_observed']} addresses in the observed cluster</strong></td>
    </tr>
    <tr>
        <th>Detected Laundering Typologies</th>
        <td><strong>{typologies_str}</strong></td>
    </tr>
</table>

<div class="section-title">4. RECOMMENDED INVESTIGATIVE ACTIONS</div>
<div class="recommendations-box">
    <p style="margin-top: 0; font-weight: bold; color: #1e40af;">System-generated recommendations — require authorized investigator/legal review. No action is issued by this system.</p>
    <ul>
        {recommendations_html}
    </ul>
</div>

<div style="margin-top: 40px; border-top: 1px solid #cbd5e1; padding-top: 15px; font-size: 11px; color: #94a3b8; text-align: center;">
    SYNTHETIC / DEMONSTRATION OUTPUT - GENERATED VIA AIR-GAPPED FORENSIC ENGINE - NOT A LEGAL INSTRUMENT
</div>

</body>
</html>"""

        # Auto-save HTML file copy to local REPORTS_DIR and active case dossiers/
        try:
            from backend.app.core.config import REPORTS_DIR, CASES_DIR
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            html_file = REPORTS_DIR / f"{meta.get('dossier_id', f'CASE_{txid}')}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_template)

            # Also save to active case dossiers/ if available
            active_case_file = CASES_DIR / ".active_case"
            if active_case_file.is_file():
                active_case = active_case_file.read_text(encoding="utf-8").strip()
                case_dossier_dir = CASES_DIR / active_case / "dossiers"
                if case_dossier_dir.is_dir():
                    case_html_file = case_dossier_dir / f"{meta.get('dossier_id', f'CASE_{txid}')}.html"
                    with open(case_html_file, "w", encoding="utf-8") as f:
                        f.write(html_template)
        except Exception as exc:
            logger.warning(f"Could not write dossier HTML to reports: {exc}")

        return html_template

dossier_service = DossierService()
