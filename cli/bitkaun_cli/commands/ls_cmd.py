"""
List case contents command for BitKaun CLI.
Lists saved reports, dossiers, and evidence files within the active case directory.
"""

from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich import box
from ..case_context import find_active_case
from ..render import console, warning_panel


def format_size(bytes_count: int) -> str:
    """Format byte sizes into human readable units."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.1f} MB"


def execute(args: list[str] = None):
    """Execute the ls command."""
    case = find_active_case()
    if not case:
        warning_panel(
            "No Active Case",
            "You are not currently inside a BitKaun forensic case directory.\n\n"
            "To start an investigation case, run:\n"
            "  [bold green]bitkaun init <case_name>[/bold green]\n"
            "  [bold green]cd <case_name>[/bold green]"
        )
        return

    case_name = case["case_name"]
    case_root = case["case_root"]

    subfolders = [
        ("reports", "REPORT / TELEMETRY", "cyan", case["reports_dir"]),
        ("dossiers", "LEGAL DOSSIER", "magenta", case["dossiers_dir"]),
        ("evidence", "CASE EVIDENCE", "yellow", case["evidence_dir"]),
    ]

    items = []
    for subname, type_label, style, folder_path in subfolders:
        if folder_path.is_dir():
            for f in sorted(folder_path.glob("*")):
                if f.is_file() and not f.name.endswith(".tmp"):
                    stat = f.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    items.append({
                        "subfolder": subname,
                        "type_label": type_label,
                        "style": style,
                        "name": f.name,
                        "size": format_size(stat.st_size),
                        "saved_date": mtime
                    })

    console.print()
    console.print(
        Panel(
            f"[bold white]Active Case:[/] [bold yellow]{case_name}[/]   "
            f"[dim]Root:[/] [cyan]{case_root}[/]\n"
            f"[dim]Total Tracked Artifacts:[/] [bold green]{len(items)}[/bold green]",
            title="[bold green][*] CASE REPOSITORY CONTENTS[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )

    if not items:
        console.print(
            "[dim]  No saved artifacts in this case yet.\n"
            "  Run commands with [/dim][bold green]--save[/bold green][dim] (e.g. [/dim]"
            "[cyan]inspect 881920041 --save[/cyan][dim], [/dim][cyan]alerts --save[/cyan][dim]) to preserve evidence.[/dim]\n"
        )
        return

    table = Table(
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Filename", style="bold white")
    table.add_column("Type", justify="center")
    table.add_column("Folder", style="dim cyan")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Saved Date", style="white")

    for it in items:
        badge = f"[{it['style']}]{it['type_label']}[/{it['style']}]"
        table.add_row(
            it["name"],
            badge,
            f"{it['subfolder']}/",
            it["size"],
            it["saved_date"]
        )

    console.print(table)
    console.print()
