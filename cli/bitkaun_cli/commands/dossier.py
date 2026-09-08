"""
Dossier command for BitKaun CLI.
Generates confidential Law Enforcement Agency (LEA) investigative summary.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel


def execute(args: list[str] = None):
    """Execute the dossier command."""
    if not args:
        warning_panel(
            "Missing Transaction ID",
            "Usage: [bold green]dossier <txid>[/bold green]\n"
            "Example: [cyan]dossier 932451115[/cyan] or [cyan]dossier 313050343[/cyan]"
        )
        return

    txid = args[0].strip()
    data = client.get_dossier(txid)
    if not data:
        return

    meta = data.get("investigation_metadata", {})
    case_id = meta.get("case_reference_id", f"LEA-{txid}")
    summary = data.get("executive_summary", "")
    recs = data.get("recommended_actions", [])
    evid = data.get("evidential_points", [])

    console.print()
    console.print(
        Panel(
            f"[bold red]CONFIDENTIAL - LAW ENFORCEMENT INVESTIGATIVE SUMMARY[/bold red]\n"
            f"[dim]Case ID:[/]          [bold cyan]{case_id}[/]\n"
            f"[dim]Target TxID:[/]      [bold yellow]{txid}[/]\n"
            f"[dim]Classification:[/]   [bold white]{meta.get('model_status', 'OFFLINE_VERIFIED')}[/]\n\n"
            f"[white]{summary}[/white]",
            title="[bold red][!] BITKAUN FORENSIC DOSSIER DOSSIER[/bold red]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if recs:
        t_rec = Table(
            title="[bold yellow][*] Recommended Investigative / Legal Actions[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
            header_style="bold yellow on black",
            expand=True,
        )
        t_rec.add_column("Priority", style="bold red", justify="center")
        t_rec.add_column("Action Step", style="white")

        for idx, rec in enumerate(recs):
            t_rec.add_row(f"P{idx + 1}", str(rec))

        console.print(t_rec)
    console.print()
