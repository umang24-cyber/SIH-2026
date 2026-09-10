"""
Status command for BitKaun CLI.
Queries /health on FastAPI backend and renders a styled forensic system panel.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, warning_panel
from ..case_context import find_active_case


def format_uptime(seconds: float) -> str:
    """Format seconds into readable human format."""
    secs = int(seconds)
    hours, remainder = divmod(secs, 3600)
    minutes, s = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {s}s"
    elif minutes > 0:
        return f"{minutes}m {s}s"
    return f"{s}s"


def execute(args: list[str] = None):
    """Execute the status command."""
    # Prepend active case panel if currently inside an initialized case
    case = find_active_case()
    if case:
        case_name = case["case_name"]
        created_at = case["created_at"]

        def _count_files(dir_path):
            if dir_path.is_dir():
                return len([f for f in dir_path.glob("*") if f.is_file() and not f.name.endswith(".tmp")])
            return 0

        reports_count = _count_files(case["reports_dir"])
        dossiers_count = _count_files(case["dossiers_dir"])
        evidence_count = _count_files(case["evidence_dir"])

        console.print()
        console.print(
            Panel(
                f"[bold white]Active Case:[/] [bold yellow]{case_name}[/]   "
                f"[dim]Created:[/] [white]{created_at}[/]\n"
                f"[dim]Location:[/]    [cyan]{case['case_root']}[/]\n\n"
                f"[bold white]Case Artifacts:[/] "
                f"[cyan]{reports_count}[/] reports   [dim]•[/dim] "
                f"[magenta]{dossiers_count}[/] dossiers   [dim]•[/dim] "
                f"[yellow]{evidence_count}[/] evidence items",
                title="[bold green][*] ACTIVE INVESTIGATION CASE[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    health = client.get_health()
    if not health:
        return

    status_str = health.get("status", "UNKNOWN")
    status_badge = (
        "[bold white on dark_green] ONLINE [/bold white on dark_green]"
        if status_str == "ONLINE"
        else f"[bold white on red] {status_str} [/bold white on red]"
    )

    uptime_str = format_uptime(health.get("uptime_seconds", 0))

    # Metric Table
    table = Table(
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        show_header=True,
    )
    table.add_column("Telemetry Metric", style="bold cyan", width=30)
    table.add_column("Value / State", style="white", justify="right", width=22)
    table.add_column("Forensic Scope", style="dim white")

    table.add_row(
        "Ledger Transactions",
        f"[bold yellow]{health.get('loaded_transactions', 0):,}[/bold yellow]",
        "Master on-chain UTXO database",
    )
    table.add_row(
        "Tracked Wallets",
        f"[bold yellow]{health.get('unique_wallets', 0):,}[/bold yellow]",
        "Distinct Bitcoin Base58 addresses",
    )
    table.add_row(
        "CIOH Clusters",
        f"[bold cyan]{health.get('cluster_count', 0):,}[/bold cyan]",
        "Multi-input co-ownership clusters",
    )
    table.add_row(
        "Investigative Scenarios",
        f"[bold cyan]{health.get('unique_scenarios', 0):,}[/bold cyan]",
        "Graph component crime syndicates",
    )
    table.add_row(
        "Prioritized Alerts",
        f"[bold red]{health.get('alert_count', 0):,}[/bold red]",
        "ML-ranked high-risk candidates",
    )
    table.add_row(
        "ML Forensics Engine",
        "[bold green]ACTIVE (XGBoost + IF)[/bold green]",
        "Binary + 5-Class Multiclass Typology",
    )
    table.add_row(
        "Network Engine",
        "[bold green]100% OFFLINE / AIR-GAPPED[/bold green]",
        "Zero external cloud dependencies",
    )

    content = f"""[bold white]{health.get('app_name', 'BitKaun AML Forensics API')}[/bold white]  [dim]v{health.get('version', '2.0.0')}[/dim]
[dim]Status:[/] {status_badge}   [dim]Uptime:[/] [yellow]{uptime_str}[/]   [dim]Target:[/] [cyan]{client.base_url}[/]
"""
    console.print()
    console.print(
        Panel(
            content.strip(),
            title="[bold green][*] BITKAUN SYSTEM TELEMETRY & ENGINE STATUS[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print(table)
    console.print()
