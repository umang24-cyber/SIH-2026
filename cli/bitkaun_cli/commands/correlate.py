"""
Correlate and Ingestion command for BitKaun CLI.
Supports uploading single bulk transaction files as well as merging Blockchain Ledger + P2P Network Telemetry.
"""
import io
import os
import requests
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, error_panel, warning_panel, create_forensic_table

SAMPLE_LEDGER_CSV = """txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type,scenario_id
881920041,2026-09-06 14:22:10,"[""1AtB5eWkX36d4YtQ99vK8h7G4xN19mK7p""]","[""1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b"",""1Vp4Qw98mNtK32bRx87hG21yE94xC65pK""]","[12.45]","[12.4485,0.001]",0.0005,P2PKH,live_ransomware_probe
881920042,2026-09-06 14:25:30,"[""1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b""]","[""1RansomMuleHop01_8819"",""1RansomCarryHop01_8819""]","[12.4485]","[6.2,6.248]",0.0005,P2SH,live_ransomware_probe
992019342,2026-09-06 15:10:00,"[""1PeelOriginSource99281hKx38v92""]","[""1PeelHopOneTarget99281hKx38v92"",""1PeelChangeAddressCarry99281hK""]","[50.0]","[1.5,48.4998]",0.0002,P2PKH,live_peeling_sequence
992019343,2026-09-06 15:15:12,"[""1PeelChangeAddressCarry99281hK""]","[""1PeelHopTwoTarget88291"",""1PeelChangeAddressCarry2_99""]","[48.4998]","[2.5,45.9996]",0.0002,P2PKH,live_peeling_sequence
771029341,2026-09-06 16:05:30,"[""1MixInputPartyA_981729381kKx"",""1MixInputPartyB_881729382bBx"",""1MixInputPartyC_771729383cCx"",""1MixInputPartyD_661729384dDx""]","[""1MixEqualOut1_991827391aAx"",""1MixEqualOut2_881827392bBx"",""1MixEqualOut3_771827393cCx"",""1MixEqualOut4_661827394dDx""]","[0.55,0.53,0.54,0.56]","[0.5,0.5,0.5,0.5]",0.0004,P2SH,live_coinjoin_round
551029482,2026-09-06 17:00:15,"[""1bs5iPLdFjEHkWzFAPTtMZmWAHF""]","[""1GtTjrBX92L5RL4QjKmoeuNbs9cBEYcd""]","[1572.10555491]","[1572.10528742]",0.00026749,P2WPKH,sample_licit_commerce
551029483,2026-09-06 17:05:00,"[""1GtTjrBX92L5RL4QjKmoeuNbs9cBEYcd""]","[""1xB8Dj2FBAXbRT7eQH5nSgtKME1UWusEv"",""1UMVbFq2Pxw5qYchFs7XYTux5pdY"",""1VibkBxo6dxSbu8JtUWMvG1GPE"",""1xT9NrChtpqwQdEwVU4cRBF3TK8wqVef""]","[1572.10528742]","[322.95552869,873.1272622,339.92347716,36.09822617]",0.0007932,P2SH,sample_licit_commerce
551029484,2026-09-06 17:10:00,"[""1xB8Dj2FBAXbRT7eQH5nSgtKME1UWusEv""]","[""1y8R7VY5P132SweHXBVa2GXaZrZqaH""]","[322.95552869]","[322.95499532]",0.00053337,P2PKH,sample_licit_commerce
551029485,2026-09-06 17:15:00,"[""1UMVbFq2Pxw5qYchFs7XYTux5pdY""]","[""1yTSCa9dPpXBbjfcijpBYxAdvAU8RV"",""1HKVPRRXEkoN6RzVbkJp6kjS68Yj3xgAb"",""1C7qHcuqnGb6Qiz6rsG73EjW3pPh""]","[873.1272622]","[110.65228661,523.80153197,238.67267037]",0.00077325,P2PKH,sample_licit_commerce
551029486,2026-09-06 17:20:00,"[""1VibkBxo6dxSbu8JtUWMvG1GPE""]","[""1Rwkabd3FWPY3oPXF7EcJYA83iET"",""1L8RfHSkdvtbVtRvBcYttqkvSLLX"",""1EB3fw14YHPkHtVfs7kbsc1jgM6WLhG"",""1NhucNu22XYNgT3QPGkf7wbrqo9wnDw3Vj"",""1ufCP4SGyWWfUGrN2mz1UCE7Uwz1GQ7vQx"",""1BgEcdu1FyhUYaJwXSv8fAVkJauZQb2z"",""1gnaezUF6EbpTpARNt2dBcAKmPY""]","[339.92347716]","[15.73531123,110.75560664,17.41998495,18.15967671,75.14136022,34.42161368,68.28951686]",0.00040687,P2SH,sample_licit_commerce"""

SAMPLE_NETWORK_CSV = """txid,relay_timestamp,relay_ip,relay_port,node_type,country_code,asn,isp,protocol_version,user_agent
881920041,2026-09-06 14:22:08,185.220.101.44,9050,bulletproof_host,RU,AS49981,WorldStream B.V. Bulletproof Relay,70015,/Satoshi:22.0.0/
881920042,2026-09-06 14:25:28,185.220.101.50,9050,tor_exit_node,RU,AS49981,WorldStream B.V. Bulletproof Relay,70015,/Satoshi:22.0.0/
992019342,2026-09-06 15:09:59,194.26.29.112,8333,vpn_proxy,PA,AS60068,Datacenter Transit Proxy,70015,/Satoshi:22.0.0/
992019343,2026-09-06 15:15:11,194.26.29.115,8333,vpn_proxy,PA,AS60068,Datacenter Transit Proxy,70015,/Satoshi:22.0.0/
771029341,2026-09-06 16:05:29,104.244.76.13,8333,tor_exit_node,DE,AS200651,Tor Relay Exit Operator,70015,/Satoshi:22.0.0/
551029482,2026-09-06 16:59:59,120.144.43.62,8333,residential,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/
551029483,2026-09-06 17:04:59,120.144.43.62,8333,residential,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/
551029484,2026-09-06 17:09:59,120.144.43.62,8333,residential,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/
551029485,2026-09-06 17:14:59,73.189.44.201,8333,residential,US,AS7922,Comcast Cable Communications,70015,/Satoshi:22.0.0/
551029486,2026-09-06 17:19:59,120.144.43.62,8333,residential,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/"""


def _render_scenario_card(sc: dict):
    """Render a single scenario threat evaluation card."""
    is_ill = sc.get("is_illicit", False)
    typ = sc.get("predicted_typology", "NORMAL").upper()
    badge_style = "bold red" if is_ill else "bold green"
    sc_id = sc.get("scenario_id")
    risk = sc.get("risk_score", 0) * 100
    conf = (sc.get("typology_confidence") or 0) * 100
    anom = sc.get("anomaly_score")
    anom_str = f"{anom} [{sc.get('anomaly_label')}]" if anom is not None else "N/A"

    badge_title = f"{typ} THREAT" if is_ill else f"LICIT ACTIVITY ({typ})"
    lines = [
        f"[{badge_style}]{badge_title}[/{badge_style}]  |  "
        f"[bold white]P(illicit):[/bold white] [{badge_style}]{risk:.1f}%[/{badge_style}]  |  "
        f"[bold white]Typology Conf:[/bold white] {conf:.1f}%  |  "
        f"[bold white]Isolation Forest:[/bold white] {anom_str}",
    ]
    if sc.get("typology_explanation"):
        lines.append(f"[dim]{sc['typology_explanation']}[/dim]")

    # SHAP feature attributions
    top_shap = sc.get("top_shap_attributions", [])
    if top_shap:
        shap_strs = []
        for a in top_shap[:3]:
            fname = a.get("plain_name") or a.get("feature_name")
            sval = a.get("attribution_value") if a.get("attribution_value") is not None else a.get("shap_value", 0)
            is_pos = a.get("direction") in ("ELEVATES_RISK", "RISK_INCREASING") or float(sval) > 0
            color = "red" if is_pos else "green"
            shap_strs.append(f"[{color}]{fname}: {'+' if is_pos else ''}{float(sval):.2f}[/{color}]")
        lines.append("[bold cyan]Key Factors:[/] " + "  ".join(shap_strs))

    lines.append(f"[bold green]Explore in 3D Graph:[/bold green] [underline]graph {sc_id}[/underline]")

    panel_text = "\n".join(lines)
    console.print(Panel(panel_text, title=f"[bold]Scenario: {sc_id} ({sc.get('transaction_count', 1)} txs)[/bold]", border_style="red" if is_ill else "green", box=box.ROUNDED))


def _send_single_file_upload(file_path: Path):
    """Upload and ingest a single combined ledger/transaction file."""
    url = f"{client.base_url}/api/ingest/file"
    try:
        with console.status(f"[bold green]Ingesting '{file_path.name}' & running V8 ML inference...[/bold green]"):
            with open(file_path, "rb") as f:
                resp = requests.post(url, files={"file": (file_path.name, f, "application/octet-stream")}, timeout=30)

        if resp.status_code != 200:
            error_panel("Ingestion Error", f"Server returned HTTP {resp.status_code}: {resp.text}")
            return

        data = resp.json()
        console.rule(f"[bold green]BULK INGESTION & V8 EVALUATION COMPLETE: {file_path.name}[/bold green]")

        # Summary Table
        t = Table(box=box.ROUNDED, border_style="green")
        t.add_column("Ingestion Metric", style="bold cyan")
        t.add_column("Count / State", style="bold white", justify="right")

        t.add_row("Total Transactions Ingested", str(data.get("total_ingested", 0)))
        t.add_row("Unique Records", str(data.get("unique_records", 0)))
        t.add_row("Newly Indexed Transactions", f"[bold green]{data.get('newly_indexed_records', 0)}[/bold green]")
        t.add_row("Duplicate Transactions", str(data.get("duplicate_records", 0)))
        t.add_row("Unique Wallets Added", f"+{data.get('unique_wallets_added', 0)}")
        console.print(t)

        scenarios = data.get("scenario_results", [])
        if scenarios:
            console.print(f"\n[bold green][*] V8 MACHINE LEARNING THREAT EVALUATION ({len(scenarios)} Scenario Clusters):[/bold green]")
            for sc in scenarios:
                _render_scenario_card(sc)

    except Exception as exc:
        error_panel("Connection Failed", f"Could not reach {url}: {exc}")


def _send_dual_stream_correlation(files):
    """Send two streams (ledger and network) to /api/ingest/correlate."""
    url = f"{client.base_url}/api/ingest/correlate"
    try:
        with console.status("[bold green]Merging dual-stream records & running V8 ML inference...[/bold green]"):
            resp = requests.post(url, files=files, timeout=30)

        if resp.status_code != 200:
            error_panel("Correlation Error", f"Server returned HTTP {resp.status_code}: {resp.text}")
            return

        data = resp.json()
        console.rule("[bold green]DUAL-LAYER INGESTION & V8 CORRELATION COMPLETE[/bold green]")

        # Summary Table
        t = Table(box=box.ROUNDED, border_style="green")
        t.add_column("Stream Telemetry", style="bold cyan")
        t.add_column("Count / Metric", style="bold white", justify="right")

        t.add_row("Ledger Records Ingested", str(data.get("ledger_records", 0)))
        t.add_row("Network Telemetry Records", str(data.get("network_records", 0)))
        t.add_row("Matched Correlation", f"[bold green]{data.get('matched_records', 0)} ({data.get('correlation_rate', 0)*100:.1f}%)[/bold green]")
        t.add_row("Newly Indexed Transactions", str(data.get("newly_indexed_records", 0)))
        t.add_row("Unmatched Streams", str((data.get("unmatched_ledger") or 0) + (data.get("unmatched_network") or 0)))
        console.print(t)

        scenarios = data.get("scenario_results", [])
        if scenarios:
            console.print(f"\n[bold green][*] V8 MACHINE LEARNING THREAT EVALUATION ({len(scenarios)} Scenario Clusters):[/bold green]")
            for sc in scenarios:
                _render_scenario_card(sc)

    except Exception as exc:
        error_panel("Connection Failed", f"Could not reach {url}: {exc}")


def execute(args: list[str] = None):
    """Execute correlate / upload command."""
    args = args or []

    # Case 1: Single file specified -> Batch File Ingestion
    if len(args) == 1:
        file_path = Path(args[0])
        if not file_path.exists():
            error_panel("File Not Found", f"Specified file '{file_path}' does not exist.")
            return
        _send_single_file_upload(file_path)
        return

    # Case 2: Two files specified -> Dual-Stream Correlation
    if len(args) == 2:
        ledger_path = Path(args[0])
        network_path = Path(args[1])
        if not ledger_path.exists():
            error_panel("File Not Found", f"Ledger file '{ledger_path}' does not exist.")
            return
        if not network_path.exists():
            error_panel("File Not Found", f"Network telemetry file '{network_path}' does not exist.")
            return

        with open(ledger_path, "rb") as lf, open(network_path, "rb") as nf:
            files = {
                "ledger_file": (ledger_path.name, lf, "text/csv"),
                "network_file": (network_path.name, nf, "text/csv")
            }
            _send_dual_stream_correlation(files)
        return

    # Case 3: No files specified -> Load benchmark dual-stream test pair
    console.print("[dim cyan]No file paths specified. Loading benchmark dual-stream test pair...[/dim cyan]")
    console.print("[dim]Usage: upload <single_file.csv> OR correlate <ledger.csv> <network.csv>[/dim]\n")
    default_test_dir = Path("test")
    if (default_test_dir / "sample_dual_stream_ledger.csv").exists() and (default_test_dir / "sample_dual_stream_network.csv").exists():
        ledger_data = (default_test_dir / "sample_dual_stream_ledger.csv").read_text(encoding="utf-8")
        network_data = (default_test_dir / "sample_dual_stream_network.csv").read_text(encoding="utf-8")
    else:
        ledger_data = SAMPLE_LEDGER_CSV
        network_data = SAMPLE_NETWORK_CSV
        try:
            pair_resp = requests.get(f"{client.base_url}/api/ingest/sample-pair", timeout=5)
            if pair_resp.status_code == 200:
                p_json = pair_resp.json()
                if p_json.get("ledger_csv") and p_json.get("network_csv"):
                    ledger_data = p_json["ledger_csv"]
                    network_data = p_json["network_csv"]
        except Exception:
            pass

    files = {
        "ledger_file": ("sample_ledger.csv", io.BytesIO(ledger_data.encode("utf-8")), "text/csv"),
        "network_file": ("sample_network.csv", io.BytesIO(network_data.encode("utf-8")), "text/csv")
    }
    _send_dual_stream_correlation(files)
