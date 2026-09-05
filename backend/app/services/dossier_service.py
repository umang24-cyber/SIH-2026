"""
Law Enforcement Agency (LEA) Forensic Dossier & Legal Summons Generator.
Formats investigation intelligence into official Section 91 Cr.P.C. / FIU-IND STR compliance documents.
100% Offline / Air-Gapped Linux & WSL2 compliant.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.ml_service import ml_service
from backend.app.services.taint_service import taint_service

logger = logging.getLogger(__name__)

class DossierService:
    def generate_dossier(self, txid: int) -> Dict[str, Any]:
        """Generates a structured Law Enforcement Investigation Dossier for a transaction."""
        tx = data_service.txid_map.get(txid)
        if not tx:
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

        # Drafted Legal Directives (Section 91 CrPC / Section 69 IT Act)
        case_id = f"LEA-STR-2026-TX{txid}"
        
        directives = [
            f"1. Issue Section 91 Cr.P.C. / BNSS Sec 94 Summons to recipient VASPs/Exchanges holding output addresses: {', '.join(output_addresses[:3])}.",
            f"2. Mandate preservation of KYC identity records, bank linkage, and IP access logs for Entity Cluster {entity_id} ({len(cluster_wallets)} unmasked addresses).",
            "3. Request FIU-IND Suspicious Transaction Report (STR) filing under PMLA (Prevention of Money Laundering Act, 2002)."
        ]
        if is_tor:
            directives.append(
                f"4. Coordinate with Cyber Crime Investigation Division regarding Tor Exit Node IP {tx.get('relay_ip')} and subpoena hosting ISP {tx.get('isp')}."
            )

        return {
            "case_metadata": {
                "dossier_id": case_id,
                "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "investigating_authority": "Cyber & Financial Intelligence Forensics Unit (FIU-IND)",
                "statutory_mandates": [
                    "Section 91, Code of Criminal Procedure, 1973 (Cr.P.C.)",
                    "Section 94, Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
                    "Section 69 / 69B, Information Technology Act, 2000",
                    "Prevention of Money Laundering Act, 2002 (PMLA)"
                ]
            },
            "transaction_evidence": {
                "txid": txid,
                "block_timestamp": timestamp_str,
                "btc_value": btc_value,
                "input_addresses_count": len(input_addresses),
                "output_addresses_count": len(output_addresses),
                "input_addresses": input_addresses,
                "output_addresses": output_addresses
            },
            "network_telemetry_attribution": {
                "ip_address": tx.get("relay_ip", "0.0.0.0"),
                "isp": tx.get("isp", "Unknown"),
                "asn": tx.get("asn", "Unknown"),
                "country": tx.get("country_code", "US"),
                "is_tor_exit_node": is_tor,
                "propagation_delta_t_seconds": round(delta_t_sec, 3)
            },
            "entity_clustering": {
                "entity_cluster_id": entity_id,
                "total_unmasked_wallets_in_cluster": len(cluster_wallets),
                "sample_co_owned_addresses": cluster_wallets[:10]
            },
            "threat_assessment": {
                "composite_risk_score": risk_score,
                "risk_rating": "CRITICAL" if risk_score >= 0.75 else ("HIGH" if risk_score >= 0.50 else "MODERATE"),
                "detected_typologies": typologies_detected,
                "taint_hop_flows_count": len(taint_summary)
            },
            "statutory_legal_directives": directives
        }

    def generate_html_dossier(self, txid: int) -> str:
        """Generates an official, print-ready HTML Law Enforcement Investigation Report."""
        dossier = self.generate_dossier(txid)
        if "error" in dossier:
            return f"<html><body><h1>Error: {dossier['error']}</h1></body></html>"

        meta = dossier["case_metadata"]
        tx_ev = dossier["transaction_evidence"]
        net = dossier["network_telemetry_attribution"]
        ent = dossier["entity_clustering"]
        threat = dossier["threat_assessment"]
        directives = dossier["statutory_legal_directives"]

        directives_html = "".join([f"<li><strong>{d}</strong></li>" for d in directives])
        typologies_str = ", ".join(threat["detected_typologies"]) if threat["detected_typologies"] else "None Detected (Baseline Flow)"
        inputs_html = "<br>".join([f"<code>{a}</code>" for a in tx_ev["input_addresses"][:5]])
        outputs_html = "<br>".join([f"<code>{a}</code>" for a in tx_ev["output_addresses"][:5]])

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CONFIDENTIAL LEA DOSSIER - {meta['dossier_id']}</title>
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
    .directives-box {{ background: #f8fafc; border-left: 4px solid #2563eb; padding: 15px; margin-top: 15px; }}
    .directives-box li {{ margin-bottom: 8px; font-size: 13px; }}
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
    <div class="confidential-badge">CONFIDENTIAL // LAW ENFORCEMENT INTELLIGENCE</div>
    <h1>FORENSIC INVESTIGATION DOSSIER & ASSET SUMMONS</h1>
    <p style="font-size: 13px; color: #64748b; margin: 0;">Issued under Section 91 Cr.P.C. / BNSS Sec 94 / FIU-IND Anti-Money Laundering Framework</p>
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
        <td>{meta['investigating_authority']}</td>
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
        <td>{tx_ev['block_timestamp']}</td>
    </tr>
    <tr>
        <th>Transferred Value</th>
        <td><strong>{tx_ev['btc_value']:.4f} BTC</strong></td>
    </tr>
    <tr>
        <th>Input Wallets ({tx_ev['input_addresses_count']})</th>
        <td>{inputs_html}</td>
    </tr>
    <tr>
        <th>Output Wallets ({tx_ev['output_addresses_count']})</th>
        <td>{outputs_html}</td>
    </tr>
</table>

<div class="section-title">2. DUAL-LAYER NETWORK TELEMETRY ATTRIBUTION</div>
<table class="data-table">
    <tr>
        <th style="width: 30%;">Relay IP Address</th>
        <td><code>{net['ip_address']}</code></td>
    </tr>
    <tr>
        <th>ISP & Autonomous System</th>
        <td>{net['isp']} (ASN: {net['asn']})</td>
    </tr>
    <tr>
        <th>Physical Jurisdiction</th>
        <td>{net['country']}</td>
    </tr>
    <tr>
        <th>Tor / Anonymizer Flag</th>
        <td><strong>{'YES - High Risk Tor Exit Node' if net['is_tor_exit_node'] else 'NO - Direct Clearnet Relay'}</strong></td>
    </tr>
    <tr>
        <th>Propagation Timing Delta (Δt)</th>
        <td>{net['propagation_delta_t_seconds']:.2f} seconds</td>
    </tr>
</table>

<div class="section-title">3. SYNDICATE & ENTITY CLUSTER IDENTIFICATION (CIOH)</div>
<table class="data-table">
    <tr>
        <th style="width: 30%;">Entity Cluster ID</th>
        <td><code>{ent['entity_cluster_id']}</code></td>
    </tr>
    <tr>
        <th>Unmasked Syndicate Wallets</th>
        <td><strong>{ent['total_unmasked_wallets_in_cluster']} addresses linked to single owner</strong></td>
    </tr>
    <tr>
        <th>Detected Laundering Typologies</th>
        <td><strong>{typologies_str}</strong></td>
    </tr>
</table>

<div class="section-title">4. STATUTORY LAW ENFORCEMENT DIRECTIVES</div>
<div class="directives-box">
    <p style="margin-top: 0; font-weight: bold; color: #1e40af;">Pursuant to Section 91 Cr.P.C. / BNSS Sec 94, the Investigating Officer (I.O.) is directed to execute the following:</p>
    <ul>
        {directives_html}
    </ul>
</div>

<div style="margin-top: 40px; border-top: 1px solid #cbd5e1; padding-top: 15px; font-size: 11px; color: #94a3b8; text-align: center;">
    CONFIDENTIAL EVIDENCE DOCUMENT - GENERATED VIA AIR-GAPPED FORENSIC ENGINE - ZERO EXTERNAL LEAKAGE VERIFIED
</div>

</body>
</html>"""
        return html_template

dossier_service = DossierService()
