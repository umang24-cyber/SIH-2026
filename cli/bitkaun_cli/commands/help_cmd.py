"""
Help command for BitKaun CLI.
"""

from rich.table import Table
from rich import box
from ..render import console


COMMAND_REGISTRY = [
    {
        "command": "graph",
        "syntax": "graph <scenario_id>",
        "description": "Render textual topology summary, node/edge hierarchy and high-risk syndicate components.",
    },
    {
        "command": "inspect",
        "syntax": "inspect <address | txid | sc_id>",
        "description": "Inspect a Bitcoin address dossier or detailed on-chain transaction UTXO flow.",
    },
    {
        "command": "trace",
        "syntax": "trace <src_address> <dst_address>",
        "description": "Compute multi-hop shortest transaction flow between source and destination wallets.",
    },
    {
        "command": "taint",
        "syntax": "taint <seed_address> [decay] [depth]",
        "description": "Compute forward dirty coin propagation with FIFO decay across downstream hops.",
    },
    {
        "command": "flow",
        "syntax": "flow <txid>",
        "description": "Visualize multi-input to multi-output UTXO financial value flow decomposition.",
    },
    {
        "command": "communities",
        "syntax": "communities <scenario_id>",
        "description": "Partition scenario subgraph into distinct syndicates using Greedy Modularity.",
    },
    {
        "command": "anomaly",
        "syntax": "anomaly <scenario_id>",
        "description": "Evaluate scenario cluster against the Isolation Forest unsupervised anomaly model.",
    },
    {
        "command": "search",
        "syntax": "search <query>",
        "description": "Universal query across TxID, wallet address, ASN, IP, or scenario cluster.",
    },
    {
        "command": "scenarios",
        "syntax": "scenarios [prefix] [page]",
        "description": "Paginated directory of scenario clusters with transaction counts and volumes.",
    },
    {
        "command": "alerts",
        "syntax": "alerts [pattern | --detail <id>]",
        "description": "Show ranked forensic AML candidates sorted by confidence, with TreeSHAP explanations.",
    },
    {
        "command": "benchmark",
        "syntax": "benchmark / eval",
        "description": "Displays quantitative model evaluation scorecard (Macro F1, Precision, Recall, Latency).",
    },
    {
        "command": "telemetry",
        "syntax": "telemetry / stats",
        "description": "Profile global P2P infrastructure, node type distributions, and latency metrics.",
    },
    {
        "command": "dossier",
        "syntax": "dossier <txid>",
        "description": "Generate confidential Law Enforcement Agency (LEA) investigative summary.",
    },
    {
        "command": "tor",
        "syntax": "tor [txid]",
        "description": "Profile transaction Shannon timing entropy and evasion score against Tor exit nodes.",
    },
    {
        "command": "ingest",
        "syntax": "ingest <sample <type> | raw_json>",
        "description": "Inject synthetic attack models or raw custom UTXO JSON payloads into the live graph.",
    },
    {
        "command": "correlate",
        "syntax": "correlate / upload",
        "description": "Temporal fusion correlator for multi-stream blockchain and network CSV files.",
    },
    {
        "command": "logs",
        "syntax": "logs [limit]",
        "description": "Streams live mempool and P2P network telemetry event frames.",
    },
    {
        "command": "status",
        "syntax": "status / sys / health",
        "description": "Display live system telemetry, loaded TX counts, cluster census & ML model status.",
    },
    {
        "command": "clear",
        "syntax": "clear / cls",
        "description": "Clear the terminal screen.",
    },
    {
        "command": "exit / quit",
        "syntax": "exit",
        "description": "Terminate the interactive investigation REPL session.",
    },
    {
        "command": "help",
        "syntax": "help [command]",
        "description": "Display this command index or syntax details for a specific command.",
    },
]


def execute(args: list[str] = None):
    """Execute the help command."""
    if args and len(args) > 0:
        target = args[0].lower()
        matched = [c for c in COMMAND_REGISTRY if c["command"].startswith(target)]
        if matched:
            cmd = matched[0]
            console.print(f"\n[bold green]Command:[/] [cyan]{cmd['command']}[/]")
            console.print(f"[bold green]Syntax:[/]  [yellow]{cmd['syntax']}[/]")
            console.print(f"[bold green]Usage:[/]   [white]{cmd['description']}[/]\n")
            return
        console.print(f"[yellow]No dedicated help topic for '{target}'. Showing full command list.[/]")

    table = Table(
        title="[bold green][*] BITKAUN FORENSIC REPL — COMMAND REFERENCE[/bold green]",
        title_justify="left",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        show_lines=True,
    )
    table.add_column("Command", style="bold cyan", width=14)
    table.add_column("Syntax", style="yellow", width=34)
    table.add_column("Description", style="white")

    for cmd in COMMAND_REGISTRY:
        table.add_row(cmd["command"], cmd["syntax"], cmd["description"])

    console.print()
    console.print(table)
    console.print("[dim green]Tip: You can pass arguments directly: e.g. 'status' or 'inspect 1jLgHKBTV4wPz8zugRhGrKfs6qcs'[/dim green]\n")
