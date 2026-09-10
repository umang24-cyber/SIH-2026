"""
Anomaly command for BitKaun CLI.
Evaluates scenario cluster against the Isolation Forest unsupervised anomaly model.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, warning_panel


def execute(args: list[str] = None):
    """Execute the anomaly command."""
    if not args:
        warning_panel(
            "Missing Scenario ID",
            "Usage: [bold green]anomaly <scenario_id>[/bold green]\n"
            "Example: [cyan]anomaly mixing_05121[/cyan] or [cyan]anomaly peeling_chain_04606[/cyan]"
        )
        return

    save_flag = "--save" in args
    clean_args = [a for a in args if a != "--save"]

    if not clean_args:
        warning_panel("Missing Scenario ID", "Please specify a scenario cluster ID.")
        return

    scenario_id = clean_args[0].strip()
    data = client.get_anomaly(scenario_id)
    if not data:
        return

    score = data.get("anomaly_score") if data.get("anomaly_score") is not None else data.get("anomaly_score_0_to_100", 0.0)
    level = data.get("anomaly_label") or data.get("anomaly_level", "NORMAL")
    raw = data.get("anomaly_raw_if_score") if data.get("anomaly_raw_if_score") is not None else data.get("raw_decision_function", 0.0)
    interp = data.get("anomaly_interpretation", "")
    rationale = data.get("top_deviations", [])

    color = "bold red" if score >= 70 else "bold yellow" if score >= 40 else "bold green"

    console.print()
    console.print(
        Panel(
            f"[dim]Scenario Cluster:[/]   [bold cyan]{scenario_id}[/]\n"
            f"[dim]Anomaly Rating:[/]     [{color}]{score:.2f} / 100 [{level}][/{color}]\n"
            f"[dim]Raw Decision Score:[/] [white]{raw:.4f}[/]  [dim](negative = outlier deviation)[/]\n"
            f"[dim]Model Engine:[/]       [green]ISOLATION FOREST (200 ESTIMATORS)[/]\n\n"
            f"[dim]Interpretation:[/]     [white]{interp}[/white]",
            title="[bold yellow][*] ISOLATION FOREST UNSUPERVISED ANOMALY EVALUATION[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if save_flag:
        from ..case_context import save_to_active_case
        save_to_active_case("anomaly", scenario_id, data, subfolder="reports")

    if rationale:
        table = Table(
            title="[bold green][*] Outlier Dimension Deviations[/bold green]",
            box=box.ROUNDED,
            border_style="green",
            header_style="bold green on black",
            expand=True,
        )
        table.add_column("Metric / Feature", style="bold cyan")
        table.add_column("Observed Value", style="bold yellow", justify="right")
        table.add_column("Global Baseline", style="dim white", justify="right")
        table.add_column("Deviation Direction", style="bold red")

        for dev in rationale:
            feature = dev.get("feature", "-")
            obs = f"{dev.get('observed_value', 0.0):.4f}"
            base = f"{dev.get('baseline_mean', 0.0):.4f}"
            diff = dev.get("deviation", "ELEVATED")
            table.add_row(feature, obs, base, str(diff))

        console.print(table)
    console.print()
