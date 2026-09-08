"""
Search command for BitKaun CLI.
Universal query across TxID, wallet address, ASN, IP, or scenario cluster.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel


def execute(args: list[str] = None):
    """Execute the search command."""
    if not args:
        warning_panel(
            "Missing Search Query",
            "Usage: [bold green]search <query>[/bold green]\n"
            "Example: [cyan]search AS49870[/cyan] or [cyan]search 932451115[/cyan]"
        )
        return

    query = " ".join(args).strip()
    data = client.search(query)
    if not data:
        return

    matches = data.get("matches", [])
    total_matches = data.get("total_matches", len(matches))
    match_type = data.get("match_type", "GENERAL")

    console.print()
    console.print(
        Panel(
            f"[dim]Search Query:[/]     [bold cyan]{query}[/]\n"
            f"[dim]Match Type:[/]       [bold yellow]{match_type}[/]\n"
            f"[dim]Total Hits:[/]       [bold green]{total_matches}[/] records resolved",
            title="[bold green][*] UNIVERSAL FORENSIC MULTI-ENTITY SEARCH[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if not matches:
        warning_panel("Zero Matches", f"No blockchain or telemetry records matched query '{query}'.")
        return

    table = Table(
        title="[bold green][*] Resolved Forensic Records[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("TxID", style="bold yellow", justify="right")
    table.add_column("Timestamp", style="white")
    table.add_column("Relay IP", style="cyan")
    table.add_column("ASN / ISP", style="dim cyan")
    table.add_column("Node Type", style="green")
    table.add_column("Scenario Cluster", style="magenta")

    for item in matches[:20]:
        txid = str(item.get("txid", "-"))
        ts = str(item.get("timestamp", "-"))
        net = item.get("network", {})
        ip = str(net.get("relay_ip", item.get("relay_ip", "-")))
        asn = str(net.get("asn", item.get("asn", "-")))
        node = str(net.get("node_type", item.get("node_type", "residential"))).upper()
        sc = str(item.get("scenario_id", "-"))
        table.add_row(txid, ts, ip, asn, node, sc)

    console.print(table)
    if len(matches) > 20:
        console.print(f"[dim]... and {len(matches) - 20} more records matched[/dim]")
    console.print()
