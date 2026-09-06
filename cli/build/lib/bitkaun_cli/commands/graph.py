"""
Graph command for BitKaun CLI.
Renders textual topology summary, node/edge census, and ASCII structural adjacency tree.
"""

from collections import defaultdict
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel, error_panel


def execute(args: list[str] = None):
    """Execute the graph command."""
    if not args or len(args) == 0:
        warning_panel(
            "Missing Scenario ID",
            "Usage: [bold green]graph <scenario_id>[/bold green]\n"
            "Example: [cyan]graph ransomware_03287[/cyan] or [cyan]graph peel_0001[/cyan]"
        )
        return

    scenario_id = args[0].strip()
    data = client.get_graph(scenario_id)
    if not data:
        error_panel(
            "Scenario Not Found",
            f"Scenario graph '{scenario_id}' was not found in the forensic database."
        )
        return

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Count nodes by type
    node_types = defaultdict(int)
    node_map = {}
    for n in nodes:
        ntype = n.get("type", "Unknown")
        node_types[ntype] += 1
        node_map[n.get("id")] = n

    # Count edges by type
    edge_types = defaultdict(int)
    tx_inflows = defaultdict(list)
    tx_outflows = defaultdict(list)
    tx_broadcasts = defaultdict(list)

    for e in edges:
        etype = e.get("type", "Unknown")
        edge_types[etype] += 1
        src = e.get("source")
        tgt = e.get("target")
        props = e.get("properties", {})

        if etype == "SENT":
            tx_inflows[tgt].append((src, props.get("amount_btc", 0.0)))
        elif etype == "RECEIVED":
            tx_outflows[src].append((tgt, props.get("amount_btc", 0.0)))
        elif etype == "BROADCAST":
            tx_broadcasts[tgt].append((src, props))

    console.print()
    console.print(
        Panel(
            f"[bold white]Scenario ID:[/] [bold cyan]{scenario_id}[/]   "
            f"[dim]Total Nodes:[/] [bold yellow]{len(nodes)}[/]   "
            f"[dim]Total Edges:[/] [bold yellow]{len(edges)}[/]\n"
            f"[dim]Typology Archetype:[/] [bold red]{scenario_id.split('_')[0].upper()}[/]",
            title="[bold green][*] SCENARIO ON-CHAIN TOPOLOGY SUMMARY[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    # Node & Edge Census Table
    census_table = Table(
        title="[bold green][*] Graph Component Census[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    census_table.add_column("Node Type", style="cyan", width=20)
    census_table.add_column("Count", justify="right", style="yellow", width=12)
    census_table.add_column("Relationship / Edge Type", style="cyan", width=25)
    census_table.add_column("Count", justify="right", style="yellow", width=12)

    n_keys = list(node_types.keys())
    e_keys = list(edge_types.keys())
    max_len = max(len(n_keys), len(e_keys))

    for i in range(max_len):
        nk = n_keys[i] if i < len(n_keys) else ""
        nv = str(node_types[nk]) if nk else ""
        ek = e_keys[i] if i < len(e_keys) else ""
        ev = str(edge_types[ek]) if ek else ""
        census_table.add_row(nk, nv, ek, ev)

    console.print(census_table)

    # ASCII Adjacency Tree
    tree = Tree(
        f"[bold green]◈ Scenario Structure: [cyan]{scenario_id}[/cyan][/bold green]",
        guide_style="green",
    )

    tx_nodes = [n for n in nodes if n.get("type") == "Transaction"]
    for tn in tx_nodes:
        tx_id_str = tn.get("id")
        props = tn.get("properties", {})
        txid_val = props.get("txid", tx_id_str)
        t_stamp = props.get("timestamp", "")
        fee = props.get("fee_btc", 0.0)

        tx_branch = tree.add(
            f"[bold yellow]TX {txid_val}[/bold yellow] [dim]({t_stamp}) · Fee: {fee:.8f} BTC[/dim]"
        )

        # Broadcast IP
        for ip_id, b_props in tx_broadcasts.get(tx_id_str, []):
            clean_ip = ip_id.replace("ip_", "")
            u_agent = b_props.get("user_agent", "")
            tx_branch.add(
                f"[dim]BROADCAST by[/dim] [cyan]{clean_ip}[/cyan] [dim]agent: {u_agent}[/dim]"
            )

        # Inflows
        inflow_branch = tx_branch.add("[green]◀ INFLOWS (Senders)[/green]")
        for src_addr, amt in tx_inflows.get(tx_id_str, []):
            inflow_branch.add(f"[cyan]{src_addr}[/cyan] [yellow]{format_btc(amt)}[/yellow]")

        # Outflows
        outflow_branch = tx_branch.add("[red]▶ OUTFLOWS (Recipients)[/red]")
        for dst_addr, amt in tx_outflows.get(tx_id_str, []):
            outflow_branch.add(f"[cyan]{dst_addr}[/cyan] [yellow]{format_btc(amt)}[/yellow]")

    console.print()
    console.print(tree)
    console.print()
