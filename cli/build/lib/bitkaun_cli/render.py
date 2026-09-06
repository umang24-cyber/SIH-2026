"""
Terminal styling and Rich rendering helpers for BitKaun CLI.
Visual theme: Phosphor-green forensic terminal aesthetic.
"""

import sys
import os

# Ensure UTF-8 stdout/stderr to avoid Windows charmap encoding crashes
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console(legacy_windows=False)

BANNER_ART = r"""
 [bold green]██████╗ ██╗████████╗██╗  ██╗ █████╗ ██╗   ██╗███╗   ██╗[/bold green]
 [bold green]██╔══██╗██║╚══██╔══╝██║ ██╔╝██╔══██╗██║   ██║████╗  ██║[/bold green]
 [bold green]██████╔╝██║   ██║   █████╔╝ ███████║██║   ██║██╔██╗ ██║[/bold green]
 [bold green]██╔══██╗██║   ██║   ██╔═██╗ ██╔══██║██║   ██║██║╚██╗██║[/bold green]
 [bold green]██████╔╝██║   ██║   ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║[/bold green]
 [bold green]╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/bold green]
 [bold cyan]BITCOIN AML FORENSICS & ON-CHAIN GRAPH REPL[/bold cyan] [dim]|[/dim] [green]v2.0[/green]
 [dim green]Offline In-Memory Telemetry Engine · Zero Cloud Dependencies[/dim green]
"""


def print_banner():
    """Print the BitKaun phosphor-green forensic banner."""
    console.print(BANNER_ART)
    console.print(
        Panel(
            "[bold white]Connected to BitKaun Forensics Backend[/bold white] [dim]•[/dim] "
            "[cyan]Target:[/cyan] [bold underline]http://localhost:8000[/bold underline]\n"
            "[dim]Type[/dim] [bold green]help[/bold green] [dim]to view available forensic commands, or[/dim] "
            "[bold green]exit[/bold green] [dim]to quit session.[/dim]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def error_panel(title: str, message: str):
    """Render a styled red error panel."""
    console.print(
        Panel(
            f"[bold red]{message}[/bold red]",
            title=f"[bold red][X] {title}[/bold red]",
            border_style="red",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def warning_panel(title: str, message: str):
    """Render a styled warning panel."""
    console.print(
        Panel(
            f"[bold yellow]{message}[/bold yellow]",
            title=f"[bold yellow][!] {title}[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def info_panel(title: str, message: str):
    """Render a styled info panel."""
    console.print(
        Panel(
            f"[white]{message}[/white]",
            title=f"[bold green][*] {title}[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def create_forensic_table(title: str, columns: list) -> Table:
    """Create a standardized table with the forensic theme."""
    table = Table(
        title=f"[bold green][*] {title}[/bold green]",
        title_justify="left",
        box=box.ROUNDED,
        header_style="bold green on black",
        border_style="dim green",
        show_edge=True,
    )
    for col in columns:
        if isinstance(col, tuple):
            header, justify, style = col
            table.add_column(header, justify=justify, style=style)
        else:
            table.add_column(str(col))
    return table


def format_btc(amount) -> str:
    """Format BTC amount with color highlighting."""
    try:
        val = float(amount)
        if val > 10.0:
            return f"[bold yellow]{val:,.4f} BTC[/bold yellow]"
        elif val > 0.1:
            return f"[cyan]{val:,.6f} BTC[/cyan]"
        else:
            return f"[dim white]{val:,.8f} BTC[/dim white]"
    except Exception:
        return f"{amount} BTC"


def format_severity(sev: str) -> str:
    """Format severity badge."""
    sev_upper = str(sev).upper()
    if sev_upper == "CRITICAL":
        return "[bold white on red] CRITICAL [/bold white on red]"
    elif sev_upper == "HIGH":
        return "[bold black on bright_yellow] HIGH [/bold black on bright_yellow]"
    elif sev_upper == "MEDIUM":
        return "[bold black on cyan] MEDIUM [/bold black on cyan]"
    return f"[dim]{sev}[/dim]"
