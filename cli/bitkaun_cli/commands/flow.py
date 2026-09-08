"""
Flow command for BitKaun CLI.
Visualizes multi-input to multi-output UTXO financial value decomposition.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel


def execute(args: list[str] = None):
    """Execute the flow command."""
    if not args:
        warning_panel(
            "Missing Transaction ID",
            "Usage: [bold green]flow <txid>[/bold green]\n"
            "Example: [cyan]flow 932451115[/cyan] or [cyan]flow 324013641[/cyan]"
        )
        return

    txid = args[0].strip()
    data = client.get_flow(txid)
    if not data:
        return

    summary = data.get("summary", {})
    inputs = data.get("inputs", [])
    outputs = data.get("outputs", [])

    console.print()
    console.print(
        Panel(
            f"[dim]Transaction ID:[/] [bold cyan]{txid}[/]   "
            f"[dim]Typology:[/]       [bold yellow]{data.get('inferred_typology', 'STANDARD').upper()}[/]\n"
            f"[dim]Total Inputs:[/]   {format_btc(summary.get('total_in_btc', 0.0))} ({summary.get('input_count', 0)} inputs)\n"
            f"[dim]Total Outputs:[/]  {format_btc(summary.get('total_out_btc', 0.0))} ({summary.get('output_count', 0)} outputs)\n"
            f"[dim]Mining Fee:[/]     {format_btc(summary.get('fee_btc', 0.0))} ({summary.get('fee_rate_percent', 0.0):.4f}%)",
            title="[bold green][*] UTXO FINANCIAL VALUE FLOW DECOMPOSITION[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    t_in = Table(
        title="[bold cyan][←] Source Input UTXOs[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold cyan on black",
        expand=True,
    )
    t_in.add_column("#", style="dim", justify="center")
    t_in.add_column("Input Address", style="cyan")
    t_in.add_column("Amount", style="bold yellow", justify="right")
    t_in.add_column("Entity Cluster", style="white")

    for idx, inp in enumerate(inputs):
        t_in.add_row(str(idx + 1), inp.get("address", "-"), format_btc(inp.get("amount_btc", 0.0)), inp.get("cluster_id", "-"))

    t_out = Table(
        title="[bold green][→] Destination Output UTXOs[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    t_out.add_column("#", style="dim", justify="center")
    t_out.add_column("Output Address", style="green")
    t_out.add_column("Amount", style="bold yellow", justify="right")
    t_out.add_column("Script Type", style="dim white")
    t_out.add_column("Classification", style="bold magenta")

    for idx, out in enumerate(outputs):
        t_out.add_row(
            str(idx + 1),
            out.get("address", "-"),
            format_btc(out.get("amount_btc", 0.0)),
            out.get("script_type", "P2PKH"),
            out.get("flow_type", "PAYMENT").upper()
        )

    console.print(t_in)
    console.print(t_out)
    console.print()
