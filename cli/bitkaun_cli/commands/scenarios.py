"""
Scenarios command for BitKaun CLI.
Paginated directory of scenario clusters with transaction counts and relay infrastructure.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel


def execute(args: list[str] = None):
    """Execute the scenarios command."""
    prefix = None
    page = 1

    if args:
        if args[0].isdigit():
            page = int(args[0])
        else:
            prefix = args[0].strip()
            if len(args) > 1 and args[1].isdigit():
                page = int(args[1])

    data = client.list_scenarios(prefix=prefix, page=page, page_size=20)
    if not data:
        return

    scenarios = data.get("scenarios", []) if isinstance(data, dict) else data
    total = data.get("total_scenarios", len(scenarios)) if isinstance(data, dict) else len(scenarios)

    console.print()
    console.print(
        Panel(
            f"[dim]Typology Prefix:[/] [bold cyan]{prefix or 'ALL'}[/]\n"
            f"[dim]Page Number:[/]     [bold yellow]{page}[/]   "
            f"[dim]Total Clusters:[/] [bold green]{total}[/]",
            title="[bold green][*] SCENARIO ENTITY CLUSTER DIRECTORY[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    table = Table(
        title=f"[bold green][*] Scenario Clusters (Page {page})[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Scenario ID", style="bold cyan")
    table.add_column("Transactions", style="bold yellow", justify="right")
    table.add_column("Total Volume", style="green", justify="right")
    table.add_column("Primary Node Type", style="white")

    for sc in scenarios:
        sc_id = str(sc.get("scenario_id", "-"))
        tx_count = str(sc.get("transaction_count", 0))
        vol = format_btc(sc.get("total_volume_btc", 0.0))
        node = str(sc.get("primary_node_type", "residential")).upper()
        table.add_row(sc_id, tx_count, vol, node)

    console.print(table)
    console.print()
