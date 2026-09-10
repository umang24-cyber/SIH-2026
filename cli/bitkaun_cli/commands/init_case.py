"""
Init case command for BitKaun CLI.
Initializes a new forensic investigation case directory (following Git's mental model).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from rich.panel import Panel
from rich import box
from ..render import console, warning_panel, error_panel


def execute(args: list[str] = None):
    """Execute the init command."""
    if not args or len(args) == 0:
        warning_panel(
            "Missing Case Name",
            "Usage: [bold green]bitkaun init <case_name>[/bold green]\n"
            "Example: [cyan]bitkaun init \"operation_black_lotus\"[/cyan]"
        )
        return

    case_name = " ".join(args).strip().strip('"').strip("'")
    if not case_name:
        warning_panel("Invalid Case Name", "Please specify a non-empty case name.")
        return

    from ..case_context import find_cases_dir
    cases_dir = find_cases_dir()
    case_dir = cases_dir / case_name

    # Check if case is already initialized
    dot_bitkaun = case_dir / ".bitkaun"
    case_json_file = dot_bitkaun / "case.json"
    if case_json_file.is_file():
        if cases_dir:
            try:
                (cases_dir / ".active_case").write_text(case_name, encoding="utf-8")
            except Exception:
                pass
        warning_panel(
            "Case Already Initialized",
            f"Case folder already contains an active case record:\n[cyan]{case_dir.resolve()}[/cyan]\n"
            f"[dim]Active case set to:[/dim] [bold cyan]{case_name}[/bold cyan]\n"
            f"[dim]To enter directly:[/dim] [bold green]cd \"{case_dir.resolve()}\"[/bold green]"
        )
        return

    try:
        # Create directory hierarchy
        case_dir.mkdir(parents=True, exist_ok=True)
        dot_bitkaun.mkdir(parents=True, exist_ok=True)
        (case_dir / "reports").mkdir(parents=True, exist_ok=True)
        (case_dir / "dossiers").mkdir(parents=True, exist_ok=True)
        (case_dir / "evidence").mkdir(parents=True, exist_ok=True)

        case_record = {
            "case_name": case_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "linked_scenarios": [],
            "linked_addresses": []
        }

        with open(case_json_file, "w", encoding="utf-8") as f:
            json.dump(case_record, f, indent=2)

        # Set as active case in central cases/ if present
        if cases_dir:
            try:
                (cases_dir / ".active_case").write_text(case_name, encoding="utf-8")
            except Exception:
                pass

        console.print()
        console.print(
            Panel(
                f"[bold white]Case Name:[/]        [bold yellow]{case_name}[/]\n"
                f"[bold white]Location:[/]         [cyan]{case_dir.resolve()}[/]\n"
                f"[bold white]Initialized Structure:[/]\n"
                f"  [dim]├──[/dim] [green].bitkaun/case.json[/]  [dim](Case metadata & chain-of-custody config)[/]\n"
                f"  [dim]├──[/dim] [cyan]reports/[/]           [dim](Saved command outputs & analytical queries)[/]\n"
                f"  [dim]├──[/dim] [cyan]dossiers/[/]          [dim](Courtroom dossiers & FIU-IND disclosures)[/]\n"
                f"  [dim]└──[/dim] [cyan]evidence/[/]          [dim](Case-specific ingested CSVs & network logs)[/]\n\n"
                f"[bold green]cd \"{case_name}\" to enter this case[/bold green]",
                title=f"[bold green][*] FORENSIC INVESTIGATION CASE INITIALIZED[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )
    except Exception as exc:
        error_panel("Initialization Error", f"Could not initialize case directory: {exc}")
