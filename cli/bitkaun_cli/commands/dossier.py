"""
Dossier command for BitKaun CLI.
Generates confidential Law Enforcement Agency (LEA) investigative summary,
with full support for --save into active case dossiers/ and 1-click courtroom PDF export.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel
from ..case_context import save_to_active_case


def execute(args: list[str] = None):
    """Execute the dossier command."""
    if not args:
        warning_panel(
            "Missing Transaction ID",
            "Usage: [bold green]dossier <txid> [--save][/bold green]\n"
            "Example: [cyan]dossier 932451115 --save[/cyan] or [cyan]dossier 313050343[/cyan]"
        )
        return

    save_flag = "--save" in args
    clean_args = [a for a in args if a != "--save"]

    if not clean_args:
        warning_panel("Missing Transaction ID", "Please specify a valid transaction ID.")
        return

    txid = clean_args[0].strip()
    data = client.get_dossier(txid)
    if not data:
        return

    case_meta = data.get("case_metadata", {})
    tx_ev = data.get("transaction_evidence", {})
    net_obs = data.get("network_telemetry_observation", {})
    threat = data.get("threat_assessment", {})
    cioh = data.get("entity_clustering", {})
    recs = data.get("recommended_investigative_actions", [])

    dossier_id = case_meta.get("dossier_id", f"CASE-2026-TX{txid}")
    risk_rating = threat.get("risk_rating", "HIGH")
    score = threat.get("composite_risk_score", 0.0)
    risk_color = "red" if risk_rating in ("CRITICAL", "HIGH") else "yellow" if risk_rating == "MEDIUM" else "green"

    val_btc = tx_ev.get("transferred_btc", 0.0)
    fee_btc = tx_ev.get("fee_btc", 0.0)
    relay_ip = net_obs.get("observed_relay_ip", "N/A")
    country = net_obs.get("recorded_country_code", "--")
    asn = net_obs.get("recorded_asn", "N/A")
    isp = net_obs.get("recorded_isp", "N/A")
    node_type = net_obs.get("recorded_node_type", "residential").upper()
    tor_ind = "DETECTED" if net_obs.get("tor_exit_indicator") else "NEGATIVE"
    prop_delay = net_obs.get("propagation_delta_t_seconds", 0.0)

    entity_id = cioh.get("entity_cluster_id", "N/A")
    linked_count = cioh.get("total_cioh_linked_addresses_observed", 1)

    console.print()
    console.print(
        Panel(
            f"[bold red]CONFIDENTIAL // LAW ENFORCEMENT INVESTIGATIVE SUMMARY[/bold red]\n"
            f"[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
            f"[bold white]Case ID:[/]          [bold cyan]{dossier_id}[/]   [dim]•[/dim]   [bold white]Threat Rating:[/] [{risk_color}]{risk_rating} ({score * 100:.1f}% Risk)[/{risk_color}]\n"
            f"[bold white]Target TxID:[/]      [bold yellow]{txid}[/]   [dim]•[/dim]   [bold white]Timestamp (UTC):[/] [dim]{tx_ev.get('timestamp_utc', 'N/A')}[/dim]\n"
            f"[bold white]Transferred:[/]      [bold green]{format_btc(val_btc)}[/]   [dim]•[/dim]   [bold white]Miner Fee:[/] [dim]{fee_btc:.8f} BTC[/dim]\n\n"
            f"[bold cyan][*] Observed P2P Network Telemetry (Layer-0):[/bold cyan]\n"
            f"  [dim]•[/dim] Relay IP:       [bold white]{relay_ip}[/] [dim]({country})[/dim]   [dim]•[/dim] Node Type: [bold yellow]{node_type}[/]\n"
            f"  [dim]•[/dim] ASN / ISP:      [white]{asn} · {isp}[/]\n"
            f"  [dim]•[/dim] Tor Exit Node:  [magenta]{tor_ind}[/]   [dim]•[/dim] Propagation Latency: [dim]{prop_delay * 1000:.1f} ms[/dim]\n\n"
            f"[bold cyan][*] CIOH Entity Clustering:[/bold cyan]\n"
            f"  [dim]•[/dim] Entity ID:      [white]{entity_id}[/]   [dim]•[/dim] Total Linked Wallets: [bold white]{linked_count}[/]\n\n"
            f"[dim]Courtroom PDF Link:[/] [cyan]http://localhost:8000/api/dossier/{txid}/html[/cyan]",
            title="[bold red][!] LEA PROSECUTION EVIDENCE DOSSIER[/bold red]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if recs:
        t_rec = Table(
            title="[bold yellow][*] Recommended Investigative & Legal Preservation Actions (FIU-IND)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
            header_style="bold yellow on black",
            expand=True,
        )
        t_rec.add_column("Step", style="bold red", justify="center", width=8)
        t_rec.add_column("Action Directive", style="white")

        for idx, rec in enumerate(recs):
            t_rec.add_row(f"P{idx + 1}", str(rec))

        console.print(t_rec)
    console.print()

    if save_flag:
        save_to_active_case("dossier", txid, data, subfolder="dossiers")
