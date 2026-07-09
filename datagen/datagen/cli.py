"""
CLI entrypoint for the datagen tool.
Usage:
    datagen --customers 1000 --start 2025-01-01 --end 2025-12-08 --output ./output/
    datagen --customers 1000 --start 2025-01-01 --end 2025-12-08 --output postgres://...
"""

import sys
import time
from typing import Any

import click
from dateutil.parser import parse as parse_date
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)
from rich.table import Table

from datagen.config import ScaleConfig
from datagen.core.generator import Generator
from datagen.sinks.base import BaseSink
from datagen.sinks.filesystem import FilesystemSink
from datagen.sinks.postgres import PostgresSink

console = Console()


# ---------------------------------------------------------------------------
# Sink factory
# ---------------------------------------------------------------------------


def make_sink(output: str) -> BaseSink:
    if output.startswith("postgres://") or output.startswith("postgresql://"):
        return PostgresSink(output)
    return FilesystemSink(output)


# ---------------------------------------------------------------------------
# Generation orchestrator
# ---------------------------------------------------------------------------


def run_generation(
    gen: Generator, sink: BaseSink, config: ScaleConfig
) -> dict[str, int]:
    """
    Run all generation steps in FK-safe order.

    Generation order:
      fixed catalog → customers → addresses → devices → sessions
      → orders+order_lines (combined) → shipments → shipment_lines
      → returns → return_lines → payments (after returns, for refunded logic)
      → ad impressions → ad clicks → ad conversions
    """

    _all_shipments: list[dict] = []
    _all_order_lines: list[dict] = []
    _all_returns: list[dict] = []

    total_rows = 0

    def _run(name: str, gen_fn, collect: list | None = None):
        nonlocal total_rows
        task = progress.add_task(f"[cyan]{name}", total=None, start=True)
        count = 0
        for batch in gen_fn():
            sink.write(name, batch)
            count += len(batch)
            if collect is not None:
                collect.extend(batch)
            progress.update(task, completed=count, total=max(count, 1))
        progress.update(
            task, completed=count, total=count, description=f"[green]✔ {name}"
        )
        total_rows += count

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description:<22}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        # ── Fixed catalog ────────────────────────────────────────────────────
        _run("warehouse", gen.generate_warehouses)
        _run("product_category", gen.generate_product_categories)
        _run("product", gen.generate_products)
        _run("product_variant", gen.generate_product_variants)
        _run("product_attribute", gen.generate_product_attributes)
        _run("inventory", gen.generate_inventory)
        _run("advertiser", gen.generate_advertisers)
        _run("campaign", gen.generate_campaigns)
        _run("ad_group", gen.generate_ad_groups)
        _run("ad_creative", gen.generate_ad_creatives)
        _run("keyword", gen.generate_keywords)
        _run("ad_group_keyword", gen.generate_ad_group_keywords)

        # ── Customer-driven ──────────────────────────────────────────────────
        _run("customer", gen.generate_customers)
        _run("customer_address", gen.generate_customer_addresses)
        _run("device", gen.generate_devices)
        _run("session", gen.generate_sessions)

        # ── Orders + order_lines (combined so total_amount is correct) ───────
        order_gen, line_gen = gen.generate_orders_and_lines()

        task = progress.add_task("[cyan]order", total=None, start=True)
        count = 0
        for batch in order_gen:
            sink.write("order", batch)
            count += len(batch)
            progress.update(task, completed=count, total=max(count, 1))
        progress.update(
            task, completed=count, total=count, description="[green]✔ order"
        )
        total_rows += count

        task = progress.add_task("[cyan]order_line", total=None, start=True)
        count = 0
        for batch in line_gen:
            sink.write("order_line", batch)
            count += len(batch)
            _all_order_lines.extend(batch)
            progress.update(task, completed=count, total=max(count, 1))
        progress.update(
            task, completed=count, total=count, description="[green]✔ order_line"
        )
        total_rows += count

        # ── Fulfillment ──────────────────────────────────────────────────────
        _run("shipment", gen.generate_shipments, _all_shipments)
        _run(
            "shipment_line",
            lambda: gen.generate_shipment_lines(_all_shipments, _all_order_lines),
        )

        # ── Returns (before payments so refunded logic works) ────────────────
        _run("return", lambda: gen.generate_returns(_all_shipments), _all_returns)
        _run(
            "return_line",
            lambda: gen.generate_return_lines(_all_returns, _all_order_lines),
        )

        # ── Payments (after returns) ─────────────────────────────────────────
        _run("payment", lambda: gen.generate_payments(_all_returns))

        # ── Ad events ────────────────────────────────────────────────────────
        _run("ad_impression", gen.generate_ad_impressions)
        _run("ad_click", gen.generate_ad_clicks)
        _run("ad_conversion", gen.generate_ad_conversions)

    return sink.row_counts()


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------


def print_summary(
    counts: dict[str, int], elapsed: float, output: str, sink: BaseSink
) -> None:
    table = Table(
        title="Generation Summary", show_header=True, header_style="bold magenta"
    )
    table.add_column("Table", style="cyan", no_wrap=True)
    table.add_column("Rows", style="white", justify="right")

    sizes = sink.file_sizes() if isinstance(sink, FilesystemSink) else {}
    if sizes:
        table.add_column("File Size", style="dim", justify="right")

    total = 0
    for name, count in counts.items():
        if sizes:
            table.add_row(name, f"{count:,}", sizes.get(name, ""))
        else:
            table.add_row(name, f"{count:,}")
        total += count

    table.add_section()
    if sizes:
        table.add_row("[bold]TOTAL", f"[bold]{total:,}", "")
    else:
        table.add_row("[bold]TOTAL", f"[bold]{total:,}")

    console.print()
    console.print(table)
    console.print(
        f"\n[bold green]✔ Done[/bold green]  "
        f"{total:,} rows written to [cyan]{output}[/cyan] "
        f"in [yellow]{elapsed:.1f}s[/yellow]"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--customers", required=True, type=int, help="Number of customers to generate"
)
@click.option("--start", required=True, type=str, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, type=str, help="End date (YYYY-MM-DD)")
@click.option(
    "--output", required=True, type=str, help="postgres://... or /path/to/folder/"
)
@click.option("--seed", default=42, type=int, help="Random seed (default: 42)")
@click.option(
    "--batch-size", default=1000, type=int, help="Rows per write batch (default: 1000)"
)
def main(
    customers: int, start: str, end: str, output: str, seed: int, batch_size: int
) -> None:
    """
    \b
    Datagen — Realistic OLTP data generator
    ----------------------------------------
    Generates data for the E-Commerce + Advertising schema.

    \b
    Examples:
      datagen --customers 1000 --start 2025-01-01 --end 2025-12-08 --output ./output/
      datagen --customers 5000 --start 2025-01-01 --end 2025-12-08 --output postgres://user:pass@localhost/db
    """
    console.print(
        Panel.fit(
            "[bold white]Datagen[/bold white] — E-Commerce + Advertising OLTP Generator",
            border_style="blue",
        )
    )

    try:
        start_date = parse_date(start).date()
        end_date = parse_date(end).date()
        config = ScaleConfig(
            customers=customers,
            start=start_date,
            end=end_date,
            output=output,
            seed=seed,
            batch_size=batch_size,
        )
    except (ValidationError, ValueError) as e:
        console.print(f"[bold red]✖ Invalid arguments:[/bold red] {e}")
        sys.exit(1)

    console.print(f"  [dim]customers :[/dim] [white]{config.customers:,}[/white]")
    console.print(
        f"  [dim]date range:[/dim] [white]{config.start}[/white] → [white]{config.end}[/white]"
    )
    console.print(f"  [dim]output    :[/dim] [white]{config.output}[/white]")
    console.print(f"  [dim]seed      :[/dim] [white]{config.seed}[/white]")
    console.print()

    sink = make_sink(output)

    console.log("[dim]Initializing sink...[/dim]")
    try:
        sink.initialize()
    except Exception as e:
        console.print(f"[bold red]✖ Failed to initialize sink:[/bold red] {e}")
        sys.exit(1)

    console.log("[dim]Starting generation...[/dim]")
    t0 = time.perf_counter()
    try:
        gen = Generator(config)
        counts = run_generation(gen, sink, config)
        sink.finalize()
    except Exception:
        console.print()
        console.print("[bold red]✖ Generation failed — rolling back...[/bold red]")
        console.print_exception(show_locals=False)
        try:
            sink.cleanup()
            console.print(
                "[yellow]↻ Cleanup complete. Sink left in clean state.[/yellow]"
            )
        except Exception as ce:
            console.print(f"[red]✖ Cleanup also failed: {ce}[/red]")
        sys.exit(1)

    elapsed = time.perf_counter() - t0
    print_summary(counts, elapsed, output, sink)


if __name__ == "__main__":
    main()
