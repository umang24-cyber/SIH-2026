"""
Help command for BitKaun CLI.
"""

from rich.table import Table
from rich import box
from ..render import console


COMMAND_REGISTRY = [
    {
        "command": "status",
        "syntax": "status",
        "description": "Display live system telemetry, loaded TX counts, cluster census & ML model status.",
    },
    {
        "command": "inspect",
        "syntax": "inspect <address | txid>",
        "description": "Inspect a Bitcoin address dossier or detailed on-chain transaction UTXO flow.",
    },
    {
        "command": "graph",
        "syntax": "graph <scenario_id>",
        "description": "Render textual topology summary, node/edge hierarchy and high-risk syndicate components.",
    },
    {
        "command": "trace",
        "syntax": "trace <src_address> <dst_address>",
        "description": "Compute multi-hop shortest transaction flow between source and destination wallets.",
    },
    {
        "command": "alerts",
        "syntax": "alerts [--detail <id>]",
        "description": "Show ranked forensic AML candidates sorted by confidence, with ML explanations.",
    },
    {
        "command": "clear",
        "syntax": "clear",
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
