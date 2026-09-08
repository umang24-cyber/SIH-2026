"""
Taint command for BitKaun CLI.
Computes forward dirty coin propagation with FIFO decay across downstream hops.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel, error_panel


def execute(args: list[str] = None):
    """Execute the taint command."""
    if not args:
        warning_panel(
            "Missing Seed Address",
            "Usage: [bold green]taint <seed_address> [decay_rate] [max_depth][/bold green]\n"
            "Example: [cyan]taint 14c55RuJwJivdZmEjpTDJNjcAfvLdkaH[/cyan]"
        )
        return

    seed_address = args[0].strip()
    decay_rate = float(args[1]) if len(args) > 1 else 0.85
    max_depth = int(args[2]) if len(args) > 2 else 5

    data = client.get_taint(seed_address, decay_rate=decay_rate, max_depth=max_depth)
    if not data:
        return

    wallets = data.get("contaminated_wallets", [])
    total_volume = data.get("total_tainted_volume_btc", data.get("total_tainted_btc", 0.0))

    console.print()
    console.print(
        Panel(
            f"[dim]Seed Address:[/]    [bold cyan]{seed_address}[/]\n"
            f"[dim]Decay Factor:[/]    [bold yellow]{decay_rate}[/]   "
            f"[dim]Max Depth:[/]    [bold yellow]{max_depth}[/]\n"
            f"[dim]Total Tainted:[/]   {format_btc(total_volume)}   "
            f"[dim]Wallets Contaminated:[/] [bold green]{len(wallets)}[/]",
            title="[bold red][*] FORWARD DIRTY COIN PROPAGATION (FIFO DECAY MODEL)[/bold red]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if not wallets:
        warning_panel("No Downstream Contamination", "No downstream forward contamination detected.")
        return

    table = Table(
        title="[bold green][*] Downstream Contamination Cascade[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Hop", style="bold yellow", justify="center")
    table.add_column("Via TxID", style="white", justify="right")
    table.add_column("Contaminated Wallet", style="cyan")
    table.add_column("Taint %", style="bold red", justify="right")
    table.add_column("Received Tainted BTC", style="bold yellow", justify="right")

    for w in wallets:
        depth = str(w.get("hop_distance", "-"))
        txid = str(w.get("via_txid", "-"))
        addr = str(w.get("address", "-"))
        score = w.get("taint_score", 0.0)
        pct = f"{score * 100:.1f}%" if score <= 1.0 else f"{score:.1f}%"
        vol = format_btc(w.get("received_tainted_btc", w.get("received_btc_from_seed", 0.0)))
        table.add_row(depth, txid, addr, pct, vol)

    console.print(table)
    console.print()
