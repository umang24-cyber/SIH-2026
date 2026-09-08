"""
Communities command for BitKaun CLI.
Partitions scenario subgraph into distinct syndicates/communities using Greedy Modularity.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, warning_panel


def execute(args: list[str] = None):
    """Execute the communities command."""
    if not args:
        warning_panel(
            "Missing Scenario ID",
            "Usage: [bold green]communities <scenario_id>[/bold green]\n"
            "Example: [cyan]communities peeling_chain_04606[/cyan]"
        )
        return

    scenario_id = args[0].strip()
    data = client.get_communities(scenario_id)
    if not data:
        return

    communities = data.get("communities", [])
    total_comms = data.get("community_count", len(communities))
    modularity = data.get("modularity_score", 0.0)

    console.print()
    console.print(
        Panel(
            f"[dim]Scenario Cluster:[/]   [bold cyan]{scenario_id}[/]\n"
            f"[dim]Syndicates Found:[/]   [bold green]{total_comms}[/] distinct communities\n"
            f"[dim]Modularity (Q):[/]    [bold yellow]{modularity:.4f}[/]",
            title="[bold green][*] GREEDY MODULARITY COMMUNITY SYNDICATE PARTITIONING[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    table = Table(
        title="[bold green][*] Partitioned Syndicate Groups[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Syndicate #", style="bold yellow", justify="center")
    table.add_column("Wallets", style="cyan", justify="right")
    table.add_column("Transactions", style="white", justify="right")
    table.add_column("Unique Relay IPs", style="green", justify="right")
    table.add_column("Core Anchor Node", style="dim cyan")

    for comm in communities[:25]:
        cid = str(comm.get("community_id", "-"))
        wallets = str(comm.get("wallet_count", comm.get("node_count", 0)))
        txs = str(comm.get("transaction_count", 0))
        ips = str(comm.get("ip_count", 0))
        anchor = str(comm.get("anchor_node", comm.get("primary_wallet", "-")))
        table.add_row(cid, wallets, txs, ips, anchor)

    console.print(table)
    if len(communities) > 25:
        console.print(f"[dim]... and {len(communities) - 25} more syndicates[/dim]")
    console.print()
