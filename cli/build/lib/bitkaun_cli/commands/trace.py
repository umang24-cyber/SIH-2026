"""
Trace command for BitKaun CLI.
Computes multi-hop shortest path between source and destination Bitcoin wallets
and renders each hop with forensic transaction details and typology tags.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, format_severity, warning_panel, error_panel


def execute(args: list[str] = None):
    """Execute the trace command."""
    if not args or len(args) < 2:
        warning_panel(
            "Missing Trace Endpoints",
            "Usage: [bold green]trace <src_address> <dst_address>[/bold green]\n"
            "Example: [cyan]trace 1jLgHKBTV4wPz8zugRhGrKfs6qcs 1wyjiCSKUZtym1hXSXRPnCgbHi6rhqU[/cyan]"
        )
        return

    src = args[0].strip()
    dst = args[1].strip()

    data = client.get_trace(src, dst)
    if not data:
        return

    path_found = data.get("path_found", False)
    hops = data.get("hops", [])
    total_btc = data.get("total_transferred_btc", 0.0)

    if not path_found or not hops:
        warning_panel(
            "No Path Resolved",
            f"No directed transaction flow path was found between:\n"
            f"[dim]Source:[/]      [cyan]{src}[/cyan]\n"
            f"[dim]Destination:[/] [cyan]{dst}[/cyan]\n"
            "[dim]The wallets may belong to disconnected clusters or exceed maximum search depth.[/dim]"
        )
        return

    console.print()
    console.print(
        Panel(
            f"[dim]Source:[/]      [bold cyan]{src}[/]\n"
            f"[dim]Destination:[/] [bold cyan]{dst}[/]\n"
            f"[dim]Trajectory:[/]  [bold green]PATH RESOLVED[/]   "
            f"[dim]Hop Distance:[/] [bold yellow]{len(hops)}[/]   "
            f"[dim]Total Value:[/] {format_btc(total_btc)}",
            title="[bold green][*] MULTI-HOP FORENSIC TRANSACTION TRACE[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    table = Table(
        title="[bold green][*] Directed Transaction Flow Sequence[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Hop", style="bold yellow", justify="center")
    table.add_column("From Wallet", style="cyan")
    table.add_column("To Wallet", style="cyan")
    table.add_column("TxID", style="white", justify="right")
    table.add_column("Amount", justify="right")
    table.add_column("Timestamp", style="white")
    table.add_column("Typology", justify="center")

    for h in hops:
        idx = h.get("hop_index", 1)
        f_w = h.get("from_wallet", "")
        t_w = h.get("to_wallet", "")
        txid = str(h.get("txid", ""))
        amt = h.get("amount_btc", 0.0)
        ts = h.get("timestamp", "")
        typology = h.get("flagged_typology")

        if typology:
            typ_badge = f"[bold white on red] {typology.upper()} [/bold white on red]"
        else:
            typ_badge = "[dim green]LICIT / CLEAN[/dim green]"

        table.add_row(
            f"#{idx}",
            f_w,
            t_w,
            txid,
            format_btc(amt),
            ts,
            typ_badge,
        )

    console.print(table)
    console.print()
