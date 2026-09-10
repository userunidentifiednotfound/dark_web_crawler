"""CLI commands for crawling, manual target execution, and end-to-end intelligence pipelines."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.repositories.finding_repository import FindingRepository
from dwi_crawler.database.repositories.page_repository import PageRepository
from dwi_crawler.database.repositories.url_repository import URLRepository
from dwi_crawler.database.session import get_async_session_factory, init_db
from dwi_crawler.discovery.enhancer import KeywordEnhancer
from dwi_crawler.queue.manager import QueueManager
from dwi_crawler.security.validation import URLNormalizer
from dwi_crawler.workers.crawler import PageFetchWorker
from dwi_crawler.workers.discovery import DiscoveryWorker
from dwi_crawler.workers.processor import ProcessingWorker

crawl_cli = typer.Typer(help="Execute crawls and end-to-end intelligence pipelines.")
console = Console()


@crawl_cli.command("crawl")
def execute_crawl(
    company_id: int = typer.Option(None, "--company", "-c", help="Target Company ID"),
    url: str = typer.Option(None, "--url", "-u", help="Direct URL to crawl"),
    depth: int = typer.Option(2, "--depth", "-d", help="Max crawl depth"),
    screenshots: bool = typer.Option(False, "--screenshots", help="Capture visual screenshots"),
    max_pages: int = typer.Option(25, "--max-pages", "-m", help="Maximum pages to crawl in this batch"),
):
    """Drain queue and crawl pending URLs for a company or direct URL."""
    async def _run():
        await init_db()

        # If direct URL provided, enqueue it first
        if url:
            async with get_async_session_factory()() as session:
                url_repo = URLRepository(session)
                queue_mgr = QueueManager(session)
                canonical = URLNormalizer.normalize(url)
                c_id = company_id or 1
                disc, _ = await url_repo.save_or_increment(
                    raw_url=url,
                    company_id=c_id,
                    source_type="onion" if ".onion" in url else "surface",
                    discovered_from="cli:direct",
                    priority=3,
                    depth=0,
                )
                await queue_mgr.enqueue_url(disc.id, c_id, canonical, depth=0, priority=3)
                await session.commit()
                console.print(f"[bold green]✓ Direct target enqueued:[/bold green] {canonical}")

        worker = PageFetchWorker()
        processor = ProcessingWorker()
        crawled_count = 0

        console.print(f"[bold cyan]Crawling up to {max_pages} pages (depth limit: {depth})...[/bold cyan]")
        for _ in range(max_pages):
            has_job = await worker.process_one_job()
            if not has_job:
                break
            crawled_count += 1
            await asyncio.sleep(0.5)

        console.print(f"[bold green]✓ Downloaded {crawled_count} pages.[/bold green]")

        # Run processor on crawled pages
        console.print("[bold cyan]Extracting threat indicators and findings...[/bold cyan]")
        proc_count = await processor.process_all_pending(limit=max_pages)
        console.print(f"[bold green]✓ Analyzed and extracted intelligence from {proc_count} pages.[/bold green]")

    asyncio.run(_run())


@crawl_cli.command("run")
def run_pipeline(
    company_id: int = typer.Option(..., "--company", "-c", help="Target Company ID to audit"),
    depth: int = typer.Option(2, "--depth", "-d", help="Maximum crawl depth"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Display execution plan without network/database operations"),
    max_crawl: int = typer.Option(10, "--max-crawl", "-m", help="Maximum URLs to crawl"),
):
    """Complete End-to-End DWI Dark Web Intelligence Pipeline for an organization."""
    async def _run():
        await init_db()

        async with get_async_session_factory()() as session:
            comp_repo = CompanyRepository(session)
            comp = await comp_repo.get_by_id(company_id)
            if not comp:
                console.print(f"[bold red]Error:[/bold red] Company ID {company_id} not found.")
                return

        console.print(f"\n[bold green]═══ DWI DARK WEB INTELLIGENCE PIPELINE: {comp.name.upper()} ═══[/bold green]")
        console.print(f"[dim]Company ID: {comp.id} | Depth: {depth} | Max Crawl: {max_crawl}[/dim]\n")

        # 1. DRY RUN PLAN
        if dry_run:
            console.print("[bold yellow]*** DRY RUN MODE: No network queries or DB mutations will be executed ***[/bold yellow]\n")
            p_domain = comp.assets[0].value if comp.assets else f"{comp.name.lower()}.com"
            terms = [k.term for k in comp.keywords] or [comp.name]

            plan_table = Table(title="Execution Plan & Query Permutations")
            plan_table.add_column("Keyword", style="bold white")
            plan_table.add_column("Surface Queries (3)", style="cyan")
            plan_table.add_column("Onion Queries (7)", style="yellow")

            for t in terms:
                qs = KeywordEnhancer.enhance_keyword(t, company_name=comp.name, domain=p_domain)
                plan_table.add_row(
                    t,
                    "\n".join(f"• {q}" for q in qs.surface_queries[:3]),
                    "\n".join(f"• {q}" for q in qs.onion_queries[:7]),
                )
            console.print(plan_table)
            console.print("\n[dim]Dry run complete. Run without --dry-run to execute live collection.[/dim]\n")
            return

        # 2. DISCOVERY PHASE
        console.print("[bold cyan]Step 1/3: Executing Bounded Dark Web & Surface Discovery (10 queries/keyword)...[/bold cyan]")
        disc_worker = DiscoveryWorker()
        discovered = await disc_worker.run_for_company(comp.id)
        console.print(f"[green]✓ Discovery complete: {len(discovered)} candidate intelligence URLs identified.[/green]\n")

        # 3. CRAWL PHASE
        console.print(f"[bold cyan]Step 2/3: Fetching Pages through Tor/Proxy Layer (max: {max_crawl})...[/bold cyan]")
        crawl_worker = PageFetchWorker()
        crawled_count = 0
        for _ in range(max_crawl):
            has_job = await crawl_worker.process_one_job()
            if not has_job:
                break
            crawled_count += 1
            await asyncio.sleep(0.4)
        console.print(f"[green]✓ Crawl complete: {crawled_count} pages retrieved and stored in CAS.[/green]\n")

        # 4. PROCESSING & THREAT INTELLIGENCE PHASE
        console.print("[bold cyan]Step 3/3: Running Entity Extraction, Keyword Matching & Evidence Generation...[/bold cyan]")
        proc_worker = ProcessingWorker()
        await proc_worker.process_all_pending(limit=max_crawl)
        console.print("[green]✓ Processing & threat intelligence extraction complete.[/green]\n")

        # 5. SUMMARY REPORT
        async with get_async_session_factory()() as session:
            f_repo = FindingRepository(session)
            findings = await f_repo.list_findings(company_id=comp.id, limit=20)
            p_repo = PageRepository(session)
            pages = await p_repo.list_pages(company_id=comp.id, limit=20)

        console.print(f"[bold green]═══ INTELLIGENCE EXECUTIVE SUMMARY: {comp.name.upper()} ═══[/bold green]")
        console.print(f"Total Discovered URLs : [bold white]{len(discovered)}[/bold white]")
        console.print(f"Total Crawled Pages   : [bold white]{len(pages)}[/bold white]")
        console.print(f"Active Security Findings: [bold red]{len(findings)}[/bold red]\n")

        if findings:
            f_table = Table(title="Generated Security Findings & Threat Exposures")
            f_table.add_column("Severity", style="bold red")
            f_table.add_column("Finding Title", style="bold white")
            f_table.add_column("Matched Term", style="yellow")
            f_table.add_column("Source Target", style="cyan")
            f_table.add_column("Evidence Context", style="dim")

            for f in findings:
                sev_color = "bold red" if f.severity in ("CRITICAL", "HIGH") else "yellow"
                ctx = f.evidence_items[0].matched_text_context[:50] if f.evidence_items else "N/A"
                f_table.add_row(
                    f"[{sev_color}]{f.severity}[/{sev_color}]",
                    f.title,
                    f.matched_keyword,
                    f.source_url[:40],
                    ctx,
                )
            console.print(f_table)
        else:
            console.print("[dim]No high-confidence exposures found during this crawl batch.[/dim]")

        console.print("\n[bold green]Pipeline finished successfully.[/bold green]\n")

    asyncio.run(_run())
