"""
cd / checkout / case switching command for BitKaun CLI.
Allows switching between investigation cases in the central AppData store,
listing available cases, and returning to the root/main workspace.
"""

import json
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich import box
from ..render import console, warning_panel, error_panel
from ..case_context import find_cases_dir, find_active_case, _load_case_dict


def list_all_cases():
    """Renders a rich table of all available cases in the central cases directory."""
    cases_dir = find_cases_dir()
    if not cases_dir or not cases_dir.is_dir():
        warning_panel("No Cases Directory", "No investigation cases store found.")
        return

    active_info = find_active_case()
    active_name = active_info.get("case_name") if active_info else None

    case_items = []
    for item in sorted(cases_dir.iterdir(), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True):
        if not item.is_dir() or item.name.startswith("."):
            continue
        case_data = _load_case_dict(item)
        if not case_data:
            continue

        r_count = len(list(case_data["reports_dir"].glob("*.json"))) if case_data["reports_dir"].is_dir() else 0
        d_count = len(list(case_data["dossiers_dir"].glob("*.json"))) if case_data["dossiers_dir"].is_dir() else 0
        e_count = len(list(case_data["evidence_dir"].iterdir())) if case_data["evidence_dir"].is_dir() else 0

        case_items.append({
            "name": case_data["case_name"],
            "created_at": str(case_data.get("created_at", "N/A"))[:19].replace("T", " "),
            "is_active": (case_data["case_name"] == active_name),
            "reports": r_count,
            "dossiers": d_count,
            "evidence": e_count,
            "total": r_count + d_count + e_count,
            "path": item
        })

    if not case_items:
        console.print(
            Panel(
                "[yellow]No investigation cases found.[/yellow]\n"
                "Run [bold green]bitkaun init <case_name>[/bold green] to create your first case.",
                title="[*] INVESTIGATION CASES",
                border_style="yellow",
                box=box.ROUNDED
            )
        )
        return

    table = Table(
        title="[*] REGISTERED INVESTIGATION CASES",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_header=True
    )
    table.add_column("Status", style="bold green", width=12)
    table.add_column("Case Name", style="bold yellow")
    table.add_column("Created At", style="dim")
    table.add_column("Reports", justify="right")
    table.add_column("Dossiers", justify="right")
    table.add_column("Total Artifacts", justify="right")

    for c in case_items:
        status_badge = "[bold green]* ACTIVE[/bold green]" if c["is_active"] else "[dim]INACTIVE[/dim]"
        name_style = f"[bold cyan]{c['name']}[/bold cyan]" if c["is_active"] else c["name"]
        table.add_row(
            status_badge,
            name_style,
            c["created_at"],
            str(c["reports"]),
            str(c["dossiers"]),
            str(c["total"])
        )

    console.print()
    console.print(table)
    console.print("[dim]Switch case:[/] [bold green]cd <case_name>[/bold green]  [dim]• Exit case:[/] [bold yellow]cd ..[/bold yellow]")
    console.print()


def execute(command: str = "cd", args: list[str] = None):
    """Execute case switching or listing."""
    cases_dir = find_cases_dir()
    if not cases_dir:
        error_panel("Store Error", "Unable to locate local AppData cases directory.")
        return

    active_file = cases_dir / ".active_case"

    # If called as 'cases', list all cases
    if command in ("cases",) or (not args and command in ("case",)):
        list_all_cases()
        return

    # If 'cd' with no args, show current active case and list all
    if not args or len(args) == 0:
        active_info = find_active_case()
        if active_info:
            console.print(f"[bold green][*] Current Active Case:[/] [bold cyan]{active_info['case_name']}[/bold cyan]")
        list_all_cases()
        return

    target = " ".join(args).strip().strip('"').strip("'")

    # Handle navigation back / out
    if target in ("..", "~", "/", "main", "none", "unset", "exit"):
        if active_file.is_file():
            try:
                active_file.unlink()
            except Exception:
                active_file.write_text("", encoding="utf-8")
        console.print()
        console.print(
            Panel(
                "[bold white]Returned to master workspace.[/bold white]\n"
                "[dim]No active case selected.[/dim]\n\n"
                "[dim]To select a case:[/] [bold green]cd <case_name>[/bold green] [dim]or type[/dim] [bold green]cases[/bold green]",
                title="[*] EXITED INVESTIGATION CASE",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )
        return

    # Target is a case name
    case_dir = cases_dir / target
    case_json = case_dir / ".bitkaun" / "case.json"

    if not case_dir.is_dir() or not case_json.is_file():
        # Case doesn't exist; offer suggestions
        warning_panel(
            "Case Not Found",
            f"No investigation case named [bold red]'{target}'[/bold red] exists in:\n"
            f"[dim]{cases_dir.resolve()}[/dim]\n\n"
            f"[dim]To create it, run:[/dim] [bold green]init {target}[/bold green]\n"
            f"[dim]To see all available cases, run:[/dim] [bold cyan]cases[/bold cyan]"
        )
        return

    # Set as active case
    try:
        active_file.write_text(target, encoding="utf-8")
    except Exception as exc:
        error_panel("Activation Error", f"Could not update active case: {exc}")
        return

    # Load stats
    case_data = _load_case_dict(case_dir)
    r_count = len(list(case_data["reports_dir"].glob("*.json"))) if case_data and case_data["reports_dir"].is_dir() else 0
    d_count = len(list(case_data["dossiers_dir"].glob("*.json"))) if case_data and case_data["dossiers_dir"].is_dir() else 0
    e_count = len(list(case_data["evidence_dir"].iterdir())) if case_data and case_data["evidence_dir"].is_dir() else 0

    console.print()
    console.print(
        Panel(
            f"[bold white]Active Case:[/]     [bold cyan]{target}[/bold cyan]\n"
            f"[bold white]Location:[/]        [dim]{case_dir.resolve()}[/dim]\n"
            f"[bold white]Artifacts:[/]       [green]{r_count} reports[/green]  •  [cyan]{d_count} dossiers[/cyan]  •  [yellow]{e_count} evidence items[/yellow]\n\n"
            f"[dim]All future commands ([green]--save[/green], [cyan]ls[/cyan]) now target this case.[/dim]\n"
            f"[dim]To return to main workspace:[/] [bold yellow]cd ..[/bold yellow]",
            title="[*] ACTIVE CASE SWITCHED",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2)
        )
    )
