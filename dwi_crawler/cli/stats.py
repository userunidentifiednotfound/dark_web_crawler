"""CLI commands for system telemetry, health checks, results inspection, and configuration."""

import asyncio
import os
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select
from dwi_crawler.config.settings import get_settings
from dwi_crawler.crawling.proxy import get_proxy_manager
from dwi_crawler.database.repositories.finding_repository import FindingRepository
from dwi_crawler.database.repositories.page_repository import PageRepository
from dwi_crawler.database.session import check_db_health, get_async_session_factory, init_db
from dwi_crawler.models.company import Company
from dwi_crawler.models.finding import Entity, Finding, IntelligenceRecord
from dwi_crawler.models.page import Page, PageLink
from dwi_crawler.models.url import DiscoveredURL
from dwi_crawler.queue.manager import QueueManager
from dwi_crawler.storage.cas import ContentAddressableStorage

stats_cli = typer.Typer(help="System health, pipeline statistics, and intelligence inspection.")
console = Console()


@stats_cli.command("stats")
def show_stats():
    """Display comprehensive database, CAS storage, and intelligence telemetry."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            # Query counts
            c_count = (await session.execute(select(func.count(Company.id)))).scalar_one()
            u_count = (await session.execute(select(func.count(DiscoveredURL.id)))).scalar_one()
            onion_u_count = (await session.execute(select(func.count(DiscoveredURL.id)).where(DiscoveredURL.source_type == "onion"))).scalar_one()
            surface_u_count = (await session.execute(select(func.count(DiscoveredURL.id)).where(DiscoveredURL.source_type == "surface"))).scalar_one()
            p_count = (await session.execute(select(func.count(Page.id)))).scalar_one()
            l_count = (await session.execute(select(func.count(PageLink.id)))).scalar_one()
            e_count = (await session.execute(select(func.count(Entity.id)))).scalar_one()
            intel_count = (await session.execute(select(func.count(IntelligenceRecord.id)))).scalar_one()
            f_count = (await session.execute(select(func.count(Finding.id)))).scalar_one()

            q_mgr = QueueManager(session)
            q_stats = await q_mgr.get_queue_stats()

            # CAS Disk Size
            settings = get_settings()
            cas_path = Path(settings.storage_path) / "pages"
            cas_size = 0
            if cas_path.exists():
                for root, _, files in os.walk(cas_path):
                    for f in files:
                        cas_size += os.path.getsize(os.path.join(root, f))
            cas_mb = round(cas_size / (1024 * 1024), 2)

            console.print("\n[bold green]═══ DWI DARK WEB CRAWLER TELEMETRY ═══[/bold green]\n")

            db_table = Table(title="Database & Storage Intelligence")
            db_table.add_column("Metric", style="bold white")
            db_table.add_column("Value", justify="right", style="bold cyan")

            db_table.add_row("Target Companies", str(c_count))
            db_table.add_row("Discovered URLs", str(u_count))
            db_table.add_row("  ↳ Onion (.onion)", f"[yellow]{onion_u_count}[/yellow]")
            db_table.add_row("  ↳ Surface Web", f"[cyan]{surface_u_count}[/cyan]")
            db_table.add_row("Crawled Pages in CAS", str(p_count))
            db_table.add_row("CAS Disk Footprint", f"{cas_mb} MB")
            db_table.add_row("Discovered Hyperlinks", str(l_count))
            db_table.add_row("Extracted IOC Entities", str(e_count))
            db_table.add_row("Intelligence Records", str(intel_count))
            db_table.add_row("Active Security Findings", f"[bold red]{f_count}[/bold red]")
            console.print(db_table)

            q_table = Table(title="Crawl Job Queue Pipeline")
            q_table.add_column("State", style="bold white")
            q_table.add_column("Jobs", justify="right", style="bold yellow")
            for st, cnt in q_stats.items():
                q_table.add_row(st.upper(), str(cnt))
            console.print(q_table)

    asyncio.run(_run())


@stats_cli.command("health")
def check_health():
    """Verify Tor proxy reachability, database integrity, and storage paths."""
    async def _run():
        console.print("[bold cyan]Diagnosing DWI Crawler environment health...[/bold cyan]\n")
        settings = get_settings()

        # Database Check
        db_ok = await check_db_health()
        db_status = "[bold green]ONLINE[/bold green]" if db_ok else "[bold red]FAILED[/bold red]"
        console.print(f"Database Connectivity  : {db_status} ({settings.database_url})")

        # Tor Proxy Check
        proxy_mgr = get_proxy_manager()
        proxy_res = await proxy_mgr.check_health()
        if proxy_res.get("status") == "healthy":
            p_status = f"[bold green]HEALTHY[/bold green] (latency: {proxy_res.get('latency_ms')}ms)"
        else:
            p_status = f"[bold yellow]DEGRADED / UNREACHABLE[/bold yellow] ({proxy_res.get('error') or 'check Tor service'})"
        console.print(f"Tor Proxy Layer ({settings.tor_proxy_type.upper()}) : {p_status}")

        # CAS Storage Check
        storage_dir = Path(settings.storage_path)
        storage_dir.mkdir(parents=True, exist_ok=True)
        s_status = "[bold green]WRITABLE[/bold green]" if os.access(storage_dir, os.W_OK) else "[bold red]READ-ONLY[/bold red]"
        console.print(f"CAS Storage Root       : {s_status} ({storage_dir.resolve()})")
        console.print(f"Scope Policy Mode      : [bold white]{settings.scope_policy}[/bold white]")
        console.print(f"Max Crawl Depth        : [bold white]{settings.max_depth}[/bold white]\n")

    asyncio.run(_run())


@stats_cli.command("config")
def show_config():
    """Display current runtime configuration without leaking secrets."""
    settings = get_settings()
    console.print("\n[bold green]═══ DWI RUNTIME CONFIGURATION ═══[/bold green]")
    table = Table()
    table.add_column("Setting", style="bold white")
    table.add_column("Active Value", style="cyan")

    table.add_row("Database URL", settings.database_url)
    table.add_row("Storage Path", str(settings.storage_path))
    table.add_row("Tor Proxy Host", settings.tor_proxy_host)
    table.add_row("Tor Proxy Port", str(settings.tor_proxy_port))
    table.add_row("Tor Proxy Type", settings.tor_proxy_type)
    table.add_row("Proxy for Onion", str(settings.use_proxy_for_onion))
    table.add_row("Proxy for Surface", str(settings.use_proxy_for_surface))
    table.add_row("Scope Policy", settings.scope_policy)
    table.add_row("Max Depth", str(settings.max_depth))
    table.add_row("Max Global Concurrency", str(settings.max_global_concurrency))
    table.add_row("Max Concurrency Per Host", str(settings.max_per_host_concurrency))
    table.add_row("Request Timeout", f"{settings.request_timeout}s")
    table.add_row("Max Response Size", f"{round(settings.max_response_bytes / (1024*1024), 2)} MB")
    table.add_row("DWI Core API URL", settings.dwi_api_url or "None")
    table.add_row("DWI API Key", "***CONFIGURED***" if settings.dwi_api_key else "None")
    console.print(table)


# --- Subcommand Group: Result, Links, Download ---
result_app = typer.Typer(name="result", help="Inspect intelligence findings and discovered results.")


@result_app.command("list")
def list_results(
    company_id: int = typer.Option(None, "--company", "-c", help="Filter by Company ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results to display"),
):
    """List actionable security findings and threat exposures."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = FindingRepository(session)
            findings = await repo.list_findings(company_id=company_id, limit=limit)

            if not findings:
                console.print("[yellow]No security findings registered yet.[/yellow]")
                return

            table = Table(title=f"Security Findings ({len(findings)} found)")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Severity", style="bold red")
            table.add_column("Title", style="bold white")
            table.add_column("Keyword", style="yellow")
            table.add_column("Source Target", style="cyan")
            table.add_column("Detected At", style="dim")

            for f in findings:
                sev_color = "bold red" if f.severity in ("CRITICAL", "HIGH") else "yellow"
                table.add_row(
                    str(f.id),
                    f"[{sev_color}]{f.severity}[/{sev_color}]",
                    f.title,
                    f.matched_keyword,
                    f.source_url[:35],
                    f.created_at.strftime("%Y-%m-%d %H:%M"),
                )
            console.print(table)

    asyncio.run(_run())


@result_app.command("show")
def show_result(finding_id: int = typer.Argument(..., help="Finding ID")):
    """Display comprehensive evidence and context for a finding."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = FindingRepository(session)
            f = await repo.get_finding(finding_id)
            if not f:
                console.print(f"[bold red]Error:[/bold red] Finding ID {finding_id} not found.")
                return

            console.print(f"\n[bold green]═══ FINDING DETAILS: {f.title} (ID: {f.id}) ═══[/bold green]")
            console.print(f"[bold]Severity:[/bold] {f.severity} | [bold]Status:[/bold] {f.status} | [bold]Confidence:[/bold] {int(f.confidence*100)}%")
            console.print(f"[bold]Matched Keyword:[/bold] {f.matched_keyword}")
            console.print(f"[bold]Source URL:[/bold] {f.source_url}")
            console.print(f"[bold]First Seen:[/bold] {f.first_seen}")

            console.print("\n[bold cyan]Immutable Evidence Records:[/bold cyan]")
            for ev in f.evidence_items:
                console.print(f"• [bold]Content SHA256:[/bold] {ev.content_hash}")
                console.print(f"  [bold]Context:[/bold] \"{ev.matched_text_context}\"")
                console.print(f"  [dim]Retrieved: {ev.retrieved_at}[/dim]\n")

    asyncio.run(_run())


links_app = typer.Typer(name="links", help="Inspect discovered page hyperlinks.")


@links_app.command("list")
def list_links(
    page_id: int = typer.Option(None, "--page", "-p", help="Filter by Source Page ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of links to show"),
):
    """List discovered hyperlinks extracted from crawled pages."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = PageRepository(session)
            links = await repo.list_links(page_id=page_id, limit=limit)

            if not links:
                console.print("[yellow]No links found.[/yellow]")
                return

            table = Table(title=f"Extracted Page Hyperlinks (showing {len(links)})")
            table.add_column("Type", style="yellow")
            table.add_column("Tag", style="cyan")
            table.add_column("Canonical Target URL", style="bold white")

            for lk in links:
                t_color = "bold yellow" if lk.is_onion else "dim"
                table.add_row(
                    f"[{t_color}]{'ONION' if lk.is_onion else 'SURFACE'}[/{t_color}]",
                    lk.link_type,
                    lk.target_canonical_url,
                )
            console.print(table)

    asyncio.run(_run())


download_app = typer.Typer(name="download", help="Inspect crawled pages stored in CAS.")


@download_app.command("list")
def list_downloads(
    company_id: int = typer.Option(None, "--company", "-c", help="Filter by Company ID"),
    limit: int = typer.Option(25, "--limit", "-l", help="Number of downloaded pages to show"),
):
    """List downloaded pages stored safely in Content Addressable Storage."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = PageRepository(session)
            pages = await repo.list_pages(company_id=company_id, limit=limit)

            if not pages:
                console.print("[yellow]No downloaded pages found in CAS.[/yellow]")
                return

            table = Table(title=f"Downloaded Pages in CAS (showing {len(pages)})")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("HTTP", style="bold white")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Content SHA256", style="dim")
            table.add_column("Canonical URL", style="bold yellow")

            for p in pages:
                table.add_row(
                    str(p.id),
                    str(p.http_status),
                    f"{round(p.content_length / 1024, 1)} KB",
                    (p.latest_content_hash or "")[:12] + "...",
                    p.canonical_url,
                )
            console.print(table)

    asyncio.run(_run())


@download_app.command("view")
def view_download(page_id: int = typer.Argument(..., help="Page ID")):
    """Display the raw page source stored in CAS for a given page ID."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = PageRepository(session)
            page = await repo.get_page(page_id)
            if not page:
                console.print(f"[bold red]Error:[/bold red] Page ID {page_id} not found.")
                return

            if not page.latest_content_hash:
                console.print(f"[yellow]No content stored for Page ID {page_id}.[/yellow]")
                return

            storage = ContentAddressableStorage()
            content = storage.retrieve_text(page.latest_content_hash, ext="html")
            if content is None:
                console.print(f"[bold red]Error:[/bold red] Content hash {page.latest_content_hash} not found in CAS storage.")
                return

            console.print(f"\n[bold green]═══ PAGE {page_id} CONTENT ({page.canonical_url}) ═══[/bold green]")
            console.print(f"[dim]SHA256: {page.latest_content_hash} | Size: {len(content)} chars[/dim]\n")
            console.print(content[:2000])
            if len(content) > 2000:
                console.print(f"\n[dim]... [truncated {len(content) - 2000} additional characters] ...[/dim]")

    asyncio.run(_run())


@download_app.command("export")
def export_download(
    page_id: int = typer.Argument(..., help="Page ID"),
    output_path: str = typer.Option(..., "--output", "-o", help="Target output file path"),
):
    """Export the raw page source from CAS to an external file."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = PageRepository(session)
            page = await repo.get_page(page_id)
            if not page or not page.latest_content_hash:
                console.print(f"[bold red]Error:[/bold red] Page ID {page_id} or content not found.")
                return

            storage = ContentAddressableStorage()
            raw_bytes = storage.retrieve_by_hash(page.latest_content_hash, ext="html")
            if raw_bytes is None:
                console.print(f"[bold red]Error:[/bold red] Content not found in CAS.")
                return

            with open(output_path, "wb") as f:
                f.write(raw_bytes)
            console.print(f"[bold green]✓ Page {page_id} exported to:[/bold green] {output_path} ({len(raw_bytes)} bytes)")

    asyncio.run(_run())
