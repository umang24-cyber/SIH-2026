"""
Correlate and Ingestion command for BitKaun CLI.
Supports uploading and merging Blockchain Ledger + P2P Network Telemetry.
"""
import io
import os
import requests
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, error_panel, create_forensic_table

SAMPLE_LEDGER_CSV = """txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type,scenario_id
881920041,2026-09-06 14:22:10,"[""1AtB5eWkX36d4YtQ99vK8h7G4xN19mK7p""]","[""1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b"",""1Vp4Qw98mNtK32bRx87hG21yE94xC65pK""]","[12.45]","[12.4485,0.001]",0.0005,P2PKH,live_ransomware_probe
881920042,2026-09-06 14:25:30,"[""1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b""]","[""1RansomMuleHop01_8819"",""1RansomCarryHop01_8819""]","[12.4485]","[6.2,6.248]",0.0005,P2SH,live_ransomware_probe
992019342,2026-09-06 15:10:00,"[""1PeelOriginSource99281hKx38v92""]","[""1PeelHopOneTarget99281hKx38v92"",""1PeelChangeAddressCarry99281hK""]","[50.0]","[1.5,48.4998]",0.0002,P2PKH,live_peeling_sequence
992019343,2026-09-06 15:15:12,"[""1PeelChangeAddressCarry99281hK""]","[""1PeelHopTwoTarget88291"",""1PeelChangeAddressCarry2_99""]","[48.4998]","[2.5,45.9996]",0.0002,P2PKH,live_peeling_sequence
771029341,2026-09-06 16:05:30,"[""1MixInputPartyA_981729381kKx"",""1MixInputPartyB_881729382bBx"",""1MixInputPartyC_771729383cCx"",""1MixInputPartyD_661729384dDx""]","[""1MixEqualOut1_991827391aAx"",""1MixEqualOut2_881827392bBx"",""1MixEqualOut3_771827393cCx"",""1MixEqualOut4_661827394dDx""]","[0.55,0.53,0.54,0.56]","[0.5,0.5,0.5,0.5]",0.0004,P2SH,live_coinjoin_round
551029482,2026-09-06 17:00:15,"[""1LicitConsumerWallet88291kKx99""]","[""1LicitMerchantStorefront77291aA"",""1LicitChangeWallet88291kKx99""]","[0.15]","[0.045,0.1049]",0.0001,P2WPKH,live_licit_purchase"""

SAMPLE_NETWORK_CSV = """txid,relay_timestamp,relay_ip,relay_port,node_type,country_code,asn,isp,protocol_version,user_agent
881920041,2026-09-06 14:22:08,185.220.101.44,9050,bulletproof_host,RU,AS49981,WorldStream B.V. Bulletproof Relay,70015,/Satoshi:22.0.0/
881920042,2026-09-06 14:25:28,185.220.101.50,9050,tor_exit_node,RU,AS49981,WorldStream B.V. Bulletproof Relay,70015,/Satoshi:22.0.0/
992019342,2026-09-06 15:09:59,194.26.29.112,8333,vpn_proxy,PA,AS60068,Datacenter Transit Proxy,70015,/Satoshi:22.0.0/
992019343,2026-09-06 15:15:11,194.26.29.115,8333,vpn_proxy,PA,AS60068,Datacenter Transit Proxy,70015,/Satoshi:22.0.0/
771029341,2026-09-06 16:05:29,104.244.76.13,8333,tor_exit_node,DE,AS200651,Tor Relay Exit Operator,70015,/Satoshi:22.0.0/
551029482,2026-09-06 17:00:15,73.189.44.201,8333,residential,US,AS7922,Comcast Cable Communications,70015,/Satoshi:22.0.0/"""


def execute(args: list[str] = None):
    """Execute correlate / upload command."""
    args = args or []

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
            _send_correlation(files)
    else:
        console.print("[dim cyan]No file paths specified. Loading benchmark dual-stream test pair...[/dim cyan]")
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
        _send_correlation(files)


def _send_correlation(files):
    url = f"{client.base_url}/api/ingest/correlate"
    try:
        with console.status("[bold green]Merging dual-stream records & running V8 ML inference...[/bold green]"):
            resp = requests.post(url, files=files, timeout=20)

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
        t.add_row("Unmatched Streams", str(data.get("unmatched_ledger", 0) + data.get("unmatched_network", 0)))
        console.print(t)

        scenarios = data.get("scenario_results", [])
        if scenarios:
            console.print(f"\n[bold green][*] V8 MACHINE LEARNING THREAT EVALUATION ({len(scenarios)} Scenario Clusters):[/bold green]")
            for sc in scenarios:
                is_ill = sc.get("is_illicit", False)
                typ = sc.get("predicted_typology", "NORMAL").upper()
                badge_style = "bold red" if is_ill else "bold green"
                sc_id = sc.get("scenario_id")
                risk = sc.get("risk_score", 0) * 100
                conf = (sc.get("typology_confidence") or 0) * 100
                anom = sc.get("anomaly_score")
                anom_str = f"{anom} [{sc.get('anomaly_label')}]" if anom is not None else "N/A"

                panel_text = (
                    f"[{badge_style}]{typ} THREAT[/{badge_style}]  |  "
                    f"[bold white]P(illicit):[/bold white] [{badge_style}]{risk:.1f}%[/{badge_style}]  |  "
                    f"[bold white]Typology Conf:[/bold white] {conf:.1f}%  |  "
                    f"[bold white]Isolation Forest:[/bold white] {anom_str}\n"
                    f"[dim]{sc.get('typology_explanation', '')}[/dim]\n"
                    f"[bold green]Explore in 3D Graph:[/bold green] [underline]graph {sc_id}[/underline]"
                )
                console.print(Panel(panel_text, title=f"[bold]Scenario: {sc_id}[/bold]", border_style="green" if not is_ill else "red", box=box.ROUNDED))

    except Exception as exc:
        error_panel("Connection Failed", f"Could not reach {url}: {exc}")
