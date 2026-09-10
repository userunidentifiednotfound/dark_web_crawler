"""CLI commands for dark web discovery and search query execution."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.session import get_async_session_factory, init_db
from dwi_crawler.discovery.search import SearchStrategy
from dwi_crawler.workers.discovery import DiscoveryWorker

search_cli = typer.Typer(help="Dark web search and intelligence discovery.")
console = Console()


@search_cli.command("run")
def run_search(
    company_id: int = typer.Option(None, "--company", "-c", help="Target Company ID"),
    keyword: str = typer.Option(None, "--keyword", "-k", help="Specific search keyword"),
    search_only: bool = typer.Option(False, "--search-only", "-s", help="Do not enqueue results for crawling"),
):
    """Execute bounded dark web and surface web searches (3 surface + 7 onion per keyword)."""
    async def _run():
        await init_db()
        worker = DiscoveryWorker()

        if company_id:
            console.print(f"[bold cyan]Running discovery for Company ID {company_id}...[/bold cyan]")
            results = await worker.run_for_company(company_id, search_only=search_only)
        elif keyword:
            console.print(f"[bold cyan]Running discovery for direct keyword: '{keyword}'...[/bold cyan]")
            strategy = SearchStrategy()
            results = await strategy.execute_discovery(keyword)
        else:
            # Run for all companies
            async with get_async_session_factory()() as session:
                repo = CompanyRepository(session)
                companies = await repo.list_companies()
            if not companies:
                console.print("[yellow]No companies configured. Register one with 'dwi-crawler company add'.[/yellow]")
                return
            results = []
            for comp in companies:
                console.print(f"[bold cyan]Running discovery for Company: {comp.name} (ID: {comp.id})...[/bold cyan]")
                res = await worker.run_for_company(comp.id, search_only=search_only)
                results.extend(res)

        table = Table(title=f"Discovered Intelligence Targets ({len(results)} found)")
        table.add_column("Type", style="yellow")
        table.add_column("URL", style="bold white")
        table.add_column("Provider", style="dim")
        table.add_column("Confidence", justify="right", style="green")

        for r in results[:40]:
            t_color = "bold yellow" if r.source_type == "onion" else "cyan"
            table.add_row(
                f"[{t_color}]{r.source_type.upper()}[/{t_color}]",
                r.url,
                r.search_provider,
                f"{int(r.confidence * 100)}%",
            )

        console.print(table)
        if not search_only:
            console.print("[bold green]✓ New candidate URLs normalized and enqueued in crawl queue.[/bold green]")

    asyncio.run(_run())


@search_cli.command("discover")
def run_discover(
    company_id: int = typer.Option(None, "--company", "-c", help="Target Company ID"),
):
    """Trigger full discovery pipeline for all registered keywords."""
    run_search(company_id=company_id, keyword=None, search_only=False)
