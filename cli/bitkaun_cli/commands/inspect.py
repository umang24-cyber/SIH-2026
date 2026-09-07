"""
Inspect command for BitKaun CLI.
Renders deep forensic dossiers on Bitcoin wallet addresses or transaction IDs.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel, error_panel


def render_transaction(tx: dict):
    """Render a comprehensive forensic transaction dossier."""
    txid = tx.get("txid")
    scenario_id = tx.get("scenario_id", "N/A")
    fee = tx.get("fee_btc", 0.0)
    script_type = tx.get("script_type", "P2PKH")
    timestamp = tx.get("timestamp", "N/A")

    net = tx.get("network") or {}
    relay_ip = net.get("relay_ip", "N/A")
    node_type = net.get("node_type", "residential")
    country = net.get("country_code", "N/A")
    asn = net.get("asn", "N/A")
    isp = net.get("isp", "N/A")
    prop_delta = net.get("propagation_delta_ms", "N/A")

    # Node type badge
    node_badge = f"[cyan]{node_type}[/cyan]"
    if "tor" in node_type.lower() or "bulletproof" in node_type.lower():
        node_badge = f"[bold white on red] {node_type.upper()} [/bold white on red]"
    elif "vpn" in node_type.lower() or "proxy" in node_type.lower():
        node_badge = f"[bold black on yellow] {node_type.upper()} [/bold black on yellow]"

    console.print()
    console.print(
        Panel(
            f"[bold white]TxID:[/] [bold yellow]{txid}[/]   "
            f"[dim]Timestamp:[/] [white]{timestamp}[/]   "
            f"[dim]Scenario:[/] [bold cyan]{scenario_id}[/]\n"
            f"[dim]Script Type:[/] [white]{script_type}[/]   "
            f"[dim]Miner Fee:[/] [yellow]{fee:.8f} BTC[/]   "
            f"[dim]Relay IP:[/] [cyan]{relay_ip}[/] ({country})   "
            f"[dim]Node Type:[/] {node_badge}",
            title="[bold green][*] ON-CHAIN TRANSACTION FORENSIC DOSSIER[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    # Telemetry Table
    net_table = Table(
        title="[bold green][*] P2P Broadcast Network Telemetry[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    net_table.add_column("Relay IP / Port", style="cyan")
    net_table.add_column("Country", style="white")
    net_table.add_column("ASN / ISP", style="white")
    net_table.add_column("Node Type", style="white")
    net_table.add_column("Propagation Delta", style="yellow")
    net_table.add_row(
        f"{relay_ip}:{net.get('relay_port', 8333)}",
        f"{country}",
        f"{asn} · {isp}",
        node_badge,
        f"{prop_delta} ms",
    )
    console.print(net_table)

    # UTXO Flow Table
    inputs = tx.get("input_addresses", [])
    in_amounts = tx.get("input_amounts", [])
    outputs = tx.get("output_addresses", [])
    out_amounts = tx.get("output_amounts", [])

    utxo_table = Table(
        title="[bold green][*] UTXO Input-to-Output Flow[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
    )
    utxo_table.add_column("Type", style="bold", width=8)
    utxo_table.add_column("Address", style="cyan", width=38)
    utxo_table.add_column("Amount", justify="right", width=22)

    total_in = 0.0
    for addr, amt in zip(inputs, in_amounts):
        utxo_table.add_row("[green]INPUT[/green]", addr, format_btc(amt))
        try:
            total_in += float(amt)
        except Exception:
            pass

    total_out = 0.0
    for addr, amt in zip(outputs, out_amounts):
        utxo_table.add_row("[red]OUTPUT[/red]", addr, format_btc(amt))
        try:
            total_out += float(amt)
        except Exception:
            pass

    utxo_table.add_section()
    utxo_table.add_row(
        "[bold white]TOTAL[/bold white]",
        f"[dim]{len(inputs)} Inputs -> {len(outputs)} Outputs[/dim]",
        f"[bold white]IN: {total_in:,.4f} | OUT: {total_out:,.4f}[/bold white]",
    )

    console.print(utxo_table)
    console.print()


def render_entity(entity: dict):
    """Render a wallet address entity dossier."""
    address = entity.get("address", "N/A")
    is_exchange = entity.get("is_licit_exchange", False)
    tx_count = entity.get("tx_count", 0)
    received = entity.get("total_received_btc", 0.0)
    sent = entity.get("total_sent_btc", 0.0)
    balance = received - sent
    first_seen = entity.get("first_seen", "N/A")
    last_seen = entity.get("last_seen", "N/A")
    scenarios = entity.get("associated_scenarios", [])

    exchange_badge = (
        "[bold black on bright_green] REGULATED EXCHANGE [/bold black on bright_green]"
        if is_exchange
        else "[bold black on cyan] PRIVATE / UNTAGGED WALLET [/bold black on cyan]"
    )

    console.print()
    console.print(
        Panel(
            f"[bold white]Address:[/] [bold cyan]{address}[/]\n"
            f"[dim]Classification:[/] {exchange_badge}\n"
            f"[dim]Associated Scenarios:[/] [yellow]{', '.join(scenarios) if scenarios else 'None (Clean)'}[/]",
            title="[bold green][*] BITCOIN WALLET DOSSIER[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    table = Table(
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
    )
    table.add_column("Metric", style="bold cyan", width=26)
    table.add_column("Value", style="white", justify="right", width=26)
    table.add_column("Forensic Significance", style="dim white")

    table.add_row(
        "Lifetime Transactions",
        f"[bold yellow]{tx_count:,}[/bold yellow]",
        "UTXO transactions involving address",
    )
    table.add_row(
        "Total Received",
        format_btc(received),
        "Inflow volume on record",
    )
    table.add_row(
        "Total Sent",
        format_btc(sent),
        "Outflow volume on record",
    )
    table.add_row(
        "Net Inflow Balance",
        format_btc(balance),
        "Estimated retained unspent value",
    )
    table.add_row(
        "First Seen",
        f"[white]{first_seen}[/white]",
        "Initial blockchain activity timestamp",
    )
    table.add_row(
        "Last Seen",
        f"[white]{last_seen}[/white]",
        "Most recent blockchain activity timestamp",
    )

    console.print(table)
    console.print()


def render_scenario(sc: dict):
    """Render a comprehensive forensic scenario cluster dossier."""
    sc_id = sc.get("scenario_id", "N/A")
    typology = sc.get("dominant_typology", "normal")
    infra_risk = sc.get("infrastructure_risk_score", 0.0)
    tx_count = sc.get("transaction_count", 0)
    in_vol = sc.get("total_input_volume_btc", 0.0)
    fees = sc.get("total_fees_btc", 0.0)
    time_win = sc.get("time_window") or {}
    start_t = time_win.get("start", "N/A")
    end_t = time_win.get("end", "N/A")
    member_txs = sc.get("member_txids", [])
    top_hubs = sc.get("top_hub_wallets", [])

    risk_style = "bold white on red" if infra_risk >= 60 else ("bold black on yellow" if infra_risk >= 30 else "bold white on green")

    console.print()
    console.print(
        Panel(
            f"[bold white]Scenario ID:[/] [bold cyan]{sc_id}[/]   "
            f"[dim]Dominant Typology:[/] [bold yellow]{typology.upper()}[/]   "
            f"[dim]Infra Risk:[/] [{risk_style}] {infra_risk:.1f}% [/{risk_style}]\n"
            f"[dim]Total Volume:[/] [yellow]{in_vol:.6f} BTC[/]   "
            f"[dim]Transactions:[/] [white]{tx_count:,}[/]   "
            f"[dim]Total Fees:[/] [white]{fees:.6f} BTC[/]\n"
            f"[dim]Observed Window:[/] [white]{start_t}[/] -> [white]{end_t}[/]",
            title="[bold green][*] SCENARIO FORENSIC CLUSTER PROFILE[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if member_txs:
        tx_table = Table(
            title="[bold green][*] Linked Scenario Transactions[/bold green]",
            box=box.ROUNDED,
            border_style="green",
            header_style="bold green on black",
            expand=True
        )
        tx_table.add_column("TxID", style="bold yellow")
        tx_table.add_column("Inspect Command", style="cyan")
        for tid in member_txs[:10]:
            tx_table.add_row(str(tid), f"inspect {tid}")
        console.print(tx_table)

    if top_hubs:
        hub_table = Table(
            title="[bold green][*] Dominant Hub Wallets[/bold green]",
            box=box.ROUNDED,
            border_style="green",
            header_style="bold green on black",
            expand=True
        )
        hub_table.add_column("Wallet Address", style="bold cyan")
        hub_table.add_column("Degree / Connections", style="white", justify="right")
        for hub in top_hubs[:8]:
            hub_table.add_row(str(hub.get("address", "")), str(hub.get("degree", 1)))
        console.print(hub_table)

    console.print(f"[dim]To visualize in 3D graph:[/dim] [bold cyan]graph {sc_id}[/bold cyan]\n")


def execute(args: list[str] = None):
    """Execute the inspect command."""
    if not args or len(args) == 0:
        warning_panel(
            "Missing Target",
            "Usage: [bold green]inspect <address | txid | scenario>[/bold green]\n"
            "Example address:  [cyan]inspect 1AtB5eWkX36d4YtQ99vK8h7G4xN19mK7p[/cyan]\n"
            "Example txid:     [cyan]inspect 881920041[/cyan]\n"
            "Example scenario: [cyan]inspect live_ransomware_probe[/cyan]"
        )
        return

    target = args[0].strip()

    # If all numeric, assume it is a TxID
    if target.isdigit():
        tx_data = client.get_transaction(int(target))
        if tx_data:
            render_transaction(tx_data)
            return

    # Check entity / address
    entity_data = client.get_entity(target)
    if entity_data:
        render_entity(entity_data)
        return

    # Check scenario cluster
    scenario_data = client.get_scenario(target)
    if scenario_data:
        render_scenario(scenario_data)
        return

    # If neither found, report clear error
    error_panel(
        "Identifier Not Found",
        f"Neither transaction, wallet address, nor scenario cluster '{target}' was found in the BitKaun ledger."
    )
