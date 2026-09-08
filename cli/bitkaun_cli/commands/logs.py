"""
Logs command for BitKaun CLI.
Streams live mempool and P2P network telemetry event frames.
"""

from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc


def execute(args: list[str] = None):
    """Execute the logs command."""
    limit = 15
    if args and args[0].isdigit():
        limit = min(max(int(args[0]), 1), 100)

    data = client.get_stream_batch(limit=limit)
    if not data:
        return

    events = data.get("events", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    table = Table(
        title=f"[bold green][*] LIVE MEMPOOL & INGESTION TELEMETRY STREAM ({len(events)} RECENT EVENTS)[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("#", style="dim", justify="center")
    table.add_column("TxID", style="bold yellow")
    table.add_column("Amount BTC", style="white", justify="right")
    table.add_column("Relay IP", style="cyan")
    table.add_column("Country", style="green", justify="center")
    table.add_column("Node Type", style="dim white")
    table.add_column("Classification", style="bold magenta")

    for idx, ev in enumerate(events):
        txid = str(ev.get("txid", "-"))
        amt = format_btc(ev.get("amount_btc", 0.0))
        ip = str(ev.get("ip_address", ev.get("relay_ip", "127.0.0.1")))
        cc = f"[{ev.get('country', '--')}]"
        node = str(ev.get("node_type", "residential")).upper()
        is_tor = ev.get("is_tor", False)
        risk_lvl = ev.get("risk_level", "LOW")
        flag = "[bold red]TOR_EXIT[/bold red]" if is_tor else f"[bold red]HIGH_RISK[/bold red]" if risk_lvl == "HIGH" else "[green]CLEAN[/green]"

        table.add_row(str(idx + 1), txid, amt, ip, cc, node, flag)

    console.print()
    console.print(table)
    console.print()
