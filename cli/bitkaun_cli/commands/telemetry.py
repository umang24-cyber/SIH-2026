"""
Telemetry / Stats command for BitKaun CLI.
Profiles global P2P infrastructure, node type distributions, and latency metrics.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console


def execute(args: list[str] = None):
    """Execute the telemetry command."""
    data = client.get_telemetry()
    if not data:
        return

    node_dist = data.get("node_type_distribution", {})
    latency = data.get("latency_by_node_type_ms", {})
    top_asns = data.get("top_asns", [])
    scripts = data.get("script_type_distribution", {})

    console.print()
    console.print(
        Panel(
            f"[dim]Total Profiled:[/] [bold cyan]{data.get('total_transactions', 0):,}[/] transactions  "
            f"[dim]Wallets:[/] [bold green]{data.get('unique_wallets', 0):,}[/]  "
            f"[dim]Scenarios:[/] [bold yellow]{data.get('unique_scenarios', 0):,}[/]",
            title="[bold green][*] GLOBAL P2P BROADCAST & NODE INFRASTRUCTURE TELEMETRY[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    t_node = Table(
        title="[bold green][*] Network Node Distribution & Propagation Latency[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    t_node.add_column("Node Classification", style="bold cyan")
    t_node.add_column("Transaction Count", style="white", justify="right")
    t_node.add_column("Share %", style="bold yellow", justify="right")
    t_node.add_column("Average Latency", style="green", justify="right")

    for node, count in node_dist.items():
        pct = f"{count / max(data.get('total_transactions', 1), 1) * 100:.1f}%"
        lat = f"{latency.get(node, 0.0):.1f} ms"
        t_node.add_row(node.replace("_", " ").title(), f"{count:,}", pct, lat)

    console.print(t_node)
    console.print()
