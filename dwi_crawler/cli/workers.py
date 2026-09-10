"""CLI commands for managing and monitoring worker processes."""

import asyncio
import time
import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from dwi_crawler.database.session import get_async_session_factory, init_db
from dwi_crawler.queue.manager import QueueManager
from dwi_crawler.workers.browser import BrowserWorker
from dwi_crawler.workers.crawler import PageFetchWorker
from dwi_crawler.workers.discovery import DiscoveryWorker
from dwi_crawler.workers.processor import ProcessingWorker

workers_app = typer.Typer(name="workers", help="Manage and monitor distributed crawler workers.")
console = Console()


@workers_app.command("start")
def start_workers(
    worker_type: str = typer.Option("all", "--type", "-t", help="Worker type: all, discovery, crawl, browser, processor"),
    concurrency: int = typer.Option(2, "--concurrency", "-c", help="Number of concurrent worker instances"),
):
    """Start crawler worker processes (discovery, crawl, browser, processor)."""
    async def _run():
        await init_db()
        console.print(f"[bold green]Starting DWI workers (type: {worker_type}, concurrency: {concurrency})...[/bold green]")

        tasks = []
        if worker_type in ("all", "discovery"):
            w = DiscoveryWorker()
            tasks.append(w.start_loop(poll_interval=20.0))

        if worker_type in ("all", "crawl"):
            for i in range(concurrency):
                w = PageFetchWorker(worker_id=f"crawler-{i+1}")
                tasks.append(w.start_loop(max_idle_sleep=2.0))

        if worker_type in ("all", "browser"):
            b = BrowserWorker()
            tasks.append(b.start_loop(poll_interval=5.0))

        if worker_type in ("all", "processor"):
            p = ProcessingWorker()
            tasks.append(p.start_loop(poll_interval=4.0))

        console.print(f"[cyan]Active workers running: {len(tasks)} tasks. Press Ctrl+C to terminate cleanly.[/cyan]")
        try:
            await asyncio.gather(*tasks)
        except (KeyboardInterrupt, asyncio.CancelledError):
            console.print("\n[yellow]Shutting down workers safely...[/yellow]")

    asyncio.run(_run())


def generate_status_table(stats: dict[str, int]) -> Table:
    table = Table(title=f"DWI Real-Time Worker & Pipeline Telemetry - {time.strftime('%H:%M:%S')}")
    table.add_column("Pipeline Stage", style="bold white")
    table.add_column("Queue Depth", justify="right", style="bold cyan")
    table.add_column("Operational Status", style="magenta")

    table.add_row("Pending Jobs", str(stats.get("pending", 0)), "[yellow]Awaiting Worker Slot[/yellow]")
    table.add_row("Active Crawls", str(stats.get("running", 0)), "[green]Processing Over Tor/HTTP[/green]")
    table.add_row("Scheduled Retries", str(stats.get("retry", 0)), "[magenta]Exponential Backoff[/magenta]")
    table.add_row("Successful Downloads", str(stats.get("success", 0)), "[bold green]Stored in CAS[/bold green]")
    table.add_row("Dead Letter Queue", str(stats.get("failed", 0)), "[red]Max Retries Exceeded[/red]")
    table.add_row("CAPTCHA Blocked", str(stats.get("captcha", 0)), "[bright_red]Pending Human Assist[/bright_red]")
    return table


@workers_app.command("status")
def workers_status(
    watch: bool = typer.Option(False, "--watch", "-w", help="Real-time live refresh monitor"),
    refresh_rate: float = typer.Option(1.5, "--refresh", "-r", help="Refresh interval in seconds"),
):
    """View operational status and live queue telemetry."""
    async def _fetch_stats():
        async with get_async_session_factory()() as session:
            mgr = QueueManager(session)
            return await mgr.get_queue_stats()

    async def _run():
        await init_db()
        if not watch:
            stats = await _fetch_stats()
            console.print(generate_status_table(stats))
            return

        with Live(console=console, screen=False, auto_refresh=False) as live:
            while True:
                try:
                    stats = await _fetch_stats()
                    live.update(generate_status_table(stats), refresh=True)
                    await asyncio.sleep(refresh_rate)
                except (KeyboardInterrupt, asyncio.CancelledError):
                    break

    asyncio.run(_run())


# Alias list to status
workers_app.command("list", help="List and inspect worker statuses.")(workers_status)
