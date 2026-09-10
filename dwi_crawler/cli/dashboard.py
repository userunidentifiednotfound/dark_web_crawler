"""Interactive CLI Text-based Dashboard for DWI Dark Web & Onion Intelligence Crawler."""

import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from sqlalchemy import func, select

from dwi_crawler.config.settings import get_settings
from dwi_crawler.crawling.proxy import get_proxy_manager
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.repositories.finding_repository import FindingRepository
from dwi_crawler.database.repositories.page_repository import PageRepository
from dwi_crawler.database.repositories.url_repository import URLRepository
from dwi_crawler.database.session import check_db_health, get_async_session_factory, init_db
from dwi_crawler.discovery.enhancer import KeywordEnhancer
from dwi_crawler.discovery.search import SearchStrategy
from dwi_crawler.models.company import Company
from dwi_crawler.models.finding import Entity, Finding, IntelligenceRecord
from dwi_crawler.models.job import CrawlJob
from dwi_crawler.models.page import Page, PageLink
from dwi_crawler.models.url import DiscoveredURL
from dwi_crawler.queue.manager import QueueManager
from dwi_crawler.security.validation import URLNormalizer
from dwi_crawler.storage.cas import ContentAddressableStorage
from dwi_crawler.workers.crawler import PageFetchWorker
from dwi_crawler.workers.discovery import DiscoveryWorker
from dwi_crawler.workers.processor import ProcessingWorker

console = Console()


def _clear():
    """Clear terminal screen if supported."""
    console.clear()


async def _fetch_telemetry():
    """Fetch current system and database telemetry counts."""
    await init_db()
    async with get_async_session_factory()() as session:
        c_count = (await session.execute(select(func.count(Company.id)))).scalar_one()
        u_count = (await session.execute(select(func.count(DiscoveredURL.id)))).scalar_one()
        onion_u = (
            await session.execute(
                select(func.count(DiscoveredURL.id)).where(DiscoveredURL.source_type == "onion")
            )
        ).scalar_one()
        surface_u = (
            await session.execute(
                select(func.count(DiscoveredURL.id)).where(DiscoveredURL.source_type == "surface")
            )
        ).scalar_one()
        p_count = (await session.execute(select(func.count(Page.id)))).scalar_one()
        l_count = (await session.execute(select(func.count(PageLink.id)))).scalar_one()
        e_count = (await session.execute(select(func.count(Entity.id)))).scalar_one()
        intel_count = (await session.execute(select(func.count(IntelligenceRecord.id)))).scalar_one()
        f_count = (await session.execute(select(func.count(Finding.id)))).scalar_one()

        q_mgr = QueueManager(session)
        q_stats = await q_mgr.get_queue_stats()

        settings = get_settings()
        cas_path = Path(settings.storage_path) / "pages"
        cas_size = 0
        if cas_path.exists():
            for root, _, files in os.walk(cas_path):
                for f in files:
                    cas_size += os.path.getsize(os.path.join(root, f))
        cas_mb = round(cas_size / (1024 * 1024), 2)

        return {
            "companies": c_count,
            "urls": u_count,
            "onion_urls": onion_u,
            "surface_urls": surface_u,
            "pages": p_count,
            "links": l_count,
            "entities": e_count,
            "intel": intel_count,
            "findings": f_count,
            "cas_mb": cas_mb,
            "queue": q_stats,
        }


def _render_header(data: dict):
    """Render top metrics banner."""
    header_table = Table.grid(expand=True)
    header_table.add_column(justify="left")
    header_table.add_column(justify="right")

    header_table.add_row(
        "[bold cyan]DWI DARK WEB & ONION INTELLIGENCE CRAWLER[/bold cyan] [dim]| CLI Operation Center[/dim]",
        f"[green]CAS: {data['cas_mb']} MB[/green] | [yellow]Onion URLs: {data['onion_urls']}[/yellow] | [red]Findings: {data['findings']}[/red]",
    )
    console.print(Panel(header_table, style="bold blue"))


def _render_overview(data: dict):
    """Render metrics table and queue status side by side."""
    layout_table = Table(show_header=False, expand=True, box=None, padding=(0, 1))
    layout_table.add_column(ratio=1)
    layout_table.add_column(ratio=1)

    # Left: Database Intel
    t_left = Table(title="[bold white]Intelligence Storage Metrics[/bold white]", expand=True)
    t_left.add_column("Indicator", style="white")
    t_left.add_column("Count", justify="right", style="bold cyan")
    t_left.add_row("Target Organizations", str(data["companies"]))
    t_left.add_row("Discovered URLs (Total)", str(data["urls"]))
    t_left.add_row("  ↳ Tor Onion (.onion)", f"[yellow]{data['onion_urls']}[/yellow]")
    t_left.add_row("  ↳ Surface Web Correlated", f"[blue]{data['surface_urls']}[/blue]")
    t_left.add_row("Crawled HTML in CAS", str(data["pages"]))
    t_left.add_row("Extracted Page Links", str(data["links"]))
    t_left.add_row("Threat Entities / IOCs", f"[magenta]{data['entities']}[/magenta]")
    t_left.add_row("Security Findings (Leaked Data)", f"[bold red]{data['findings']}[/bold red]")

    # Right: Pipeline Queue Depth
    t_right = Table(title="[bold white]Queue Pipeline Status[/bold white]", expand=True)
    t_right.add_column("Job State", style="white")
    t_right.add_column("Pending / Active", justify="right", style="bold green")

    q = data["queue"]
    t_right.add_row("PENDING (Waiting in Queue)", f"[bold yellow]{q.get('PENDING', 0)}[/bold yellow]")
    t_right.add_row("RUNNING (In Flight)", f"[bold cyan]{q.get('RUNNING', 0)}[/bold cyan]")
    t_right.add_row("SUCCESS (Crawled & Stored)", f"[green]{q.get('SUCCESS', 0)}[/green]")
    t_right.add_row("RETRY (Backoff Scheduled)", f"[orange3]{q.get('RETRY', 0)}[/orange3]")
    t_right.add_row("FAILED (Dead Letter)", f"[red]{q.get('FAILED', 0)}[/red]")
    t_right.add_row("CAPTCHA / BLOCKED", f"[magenta]{q.get('CAPTCHA', 0) + q.get('BLOCKED', 0)}[/magenta]")

    layout_table.add_row(t_left, t_right)
    console.print(layout_table)


def _render_menu():
    """Print available interactive actions."""
    menu_table = Table(title="[bold cyan]Command Options[/bold cyan]", expand=True, show_lines=False)
    menu_table.add_column("[bold yellow]Key[/bold yellow]", justify="center", style="bold yellow", width=6)
    menu_table.add_column("Operation", style="bold white", width=26)
    menu_table.add_column("Description", style="dim")

    menu_table.add_row("1", "View Security Findings", "Inspect detected data leaks, ransomware posts, and threat levels")
    menu_table.add_row("2", "View Discovered URLs & Queue", "List pending onion/surface URLs waiting to be crawled")
    menu_table.add_row("3", "View Downloaded CAS Pages", "Inspect HTML pages stored in Content Addressable Storage")
    menu_table.add_row("4", "Run End-to-End Pipeline", "Discover -> Crawl -> Process -> Extract IOCs for a company")
    menu_table.add_row("5", "Run Tor Crawl Batch", "Drain pending queue and fetch pages through Tor SOCKS5")
    menu_table.add_row("6", "Run Dark Web Discovery", "Generate bounded queries (3 surface + 7 onion) and search")
    menu_table.add_row("7", "Manage Companies & Assets", "Add or list target organizations and monitored domains")
    menu_table.add_row("8", "Check Health & Tor Proxy", "Diagnose Tor circuit, database connectivity, and CAS storage")
    menu_table.add_row("9", "Interactive Auto-Click Test", "Test auto-clicking 'I'm not a robot' / Continue / verification buttons")
    menu_table.add_row("r", "Refresh Dashboard", "Re-query database and reload current metrics")
    menu_table.add_row("q", "Quit / Exit", "Exit CLI dashboard")

    console.print(menu_table)


async def _op_view_findings():
    """List and inspect security findings."""
    async with get_async_session_factory()() as session:
        repo = FindingRepository(session)
        findings = await repo.list_findings(limit=None)
        if not findings:
            console.print("\n[yellow]No security findings registered yet.[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        table = Table(title=f"All Security Findings ({len(findings)} Total Records)")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Severity", style="bold")
        table.add_column("Title / Threat Match", style="white")
        table.add_column("Matched Keyword", style="yellow")
        table.add_column("Confidence", justify="right")
        table.add_column("Identified At", style="dim")

        for f in findings:
            sev_style = "red" if f.severity.upper() in ("CRITICAL", "HIGH") else "yellow"
            kw_match = getattr(f, "matched_keyword", "-")
            table.add_row(
                str(f.id),
                f"[{sev_style}]{f.severity.upper()}[/{sev_style}]",
                f.title,
                kw_match[:25],
                f"{f.confidence:.2f}",
                f.created_at.strftime("%Y-%m-%d %H:%M") if f.created_at else "",
            )
        console.print(table)

        f_id = Prompt.ask("\nEnter Finding ID to view deep details & inspect evidence HTML (or press Enter to return)", default="")
        if f_id.isdigit():
            target = await repo.get_finding(int(f_id))
            if not target:
                console.print(f"[red]Finding ID {f_id} not found.[/red]")
            else:
                entities = getattr(target, "entities", [])
                evidences = getattr(target, "evidence_items", getattr(target, "evidences", []))
                f_key = getattr(target, "finding_key", getattr(target, "matched_keyword", "N/A"))
                source_url = getattr(target, "source_url", "N/A")
                source_type = getattr(target, "source_type", "onion")

                info_text = (
                    f"[bold]Title:[/bold] {target.title}\n"
                    f"[bold]Severity:[/bold] {target.severity.upper()} (Confidence: {target.confidence})\n"
                    f"[bold]Description:[/bold] {target.description or 'None'}\n"
                    f"[bold]Finding Key / Matched Keyword:[/bold] {f_key}\n"
                    f"[bold]Source URL:[/bold] {source_url} ([cyan]{source_type}[/cyan])\n"
                    f"[bold]Identified At:[/bold] {target.created_at.strftime('%Y-%m-%d %H:%M:%S') if target.created_at else 'N/A'}\n"
                    f"[bold]Associated Entities (IOCs):[/bold] {len(entities)}\n"
                    f"[bold]Evidence Snapshots:[/bold] {len(evidences)}"
                )
                console.print(Panel(
                    info_text,
                    title=f"Finding Deep Dive - ID {target.id}",
                    style="bold red" if target.severity.upper() in ("CRITICAL", "HIGH") else "yellow",
                ))
                if entities:
                    e_tab = Table(title="Correlated Threat Entities (IOCs)")
                    e_tab.add_column("Type", style="cyan")
                    e_tab.add_column("Value / Indicator", style="bold white")
                    for e in entities:
                        e_tab.add_row(getattr(e, "entity_type", "IOC"), getattr(e, "value", str(e)))
                    console.print(e_tab)

                if evidences:
                    ev_tab = Table(title="Evidence Records Linked to Finding")
                    ev_tab.add_column("Evidence ID", style="cyan", justify="right")
                    ev_tab.add_column("Content SHA256", style="dim")
                    ev_tab.add_column("Source URL", style="white")
                    ev_tab.add_column("Context Snippet", style="italic")
                    for ev in evidences:
                        ev_tab.add_row(
                            str(ev.id),
                            ev.content_hash[:16] + "...",
                            ev.source_url[:40] + ("..." if len(ev.source_url) > 40 else ""),
                            ev.matched_text_context[:60] + ("..." if len(ev.matched_text_context) > 60 else ""),
                        )
                    console.print(ev_tab)

                    if Confirm.ask("Inspect raw HTML source for this finding entirely?", default=False):
                        storage = ContentAddressableStorage()
                        first_ev = evidences[0]
                        raw_html = storage.retrieve_text(first_ev.content_hash, ext="html")
                        if raw_html:
                            _inspect_raw_html_interactive(raw_html, title=f"Finding #{target.id} Evidence HTML ({first_ev.content_hash})")
                        else:
                            console.print("[yellow]Raw HTML content not found in CAS for hash:[/yellow] " + first_ev.content_hash)
            Prompt.ask("\nPress Enter to continue")


async def _op_view_queue():
    """List pending crawl jobs and URLs."""
    async with get_async_session_factory()() as session:
        q_mgr = QueueManager(session)
        jobs = await q_mgr.list_queue_jobs(limit=None)
        if not jobs:
            console.print("\n[yellow]No jobs in queue.[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        table = Table(title=f"All Crawl Queue Jobs ({len(jobs)} Total)")
        table.add_column("Job ID", style="cyan", justify="right")
        table.add_column("State", style="bold")
        table.add_column("Target URL", style="white")
        table.add_column("Priority", justify="right")
        table.add_column("Attempt / Retries", justify="right")
        table.add_column("Created At", style="dim")

        for j in jobs:
            st_color = "green" if j.status == "SUCCESS" else "yellow" if j.status == "PENDING" else "red"
            attempts = getattr(j, "attempt", getattr(j, "retry_count", 0))
            max_r = getattr(j, "max_retries", 4)
            created_str = j.created_at.strftime("%H:%M:%S") if getattr(j, "created_at", None) else ""
            table.add_row(
                str(j.id),
                f"[{st_color}]{j.status}[/{st_color}]",
                j.url[:70] + ("..." if len(j.url) > 70 else ""),
                str(j.priority),
                f"{attempts}/{max_r}",
                created_str,
            )
        console.print(table)
        Prompt.ask("\nPress Enter to continue")


def _inspect_raw_html_interactive(content: str, title: str = "Raw HTML"):
    """Interactive helper to inspect entire raw HTML or search/find within it."""
    console.print(Panel(
        f"[bold cyan]{title}[/bold cyan]\n"
        f"Total Size: {len(content)} characters | {len(content.encode('utf-8'))} bytes | {len(content.splitlines())} lines\n\n"
        f"Choose inspection mode:\n"
        f"  [bold yellow]1[/bold yellow] - Display Entire Raw HTML (complete un-truncated source)\n"
        f"  [bold yellow]2[/bold yellow] - Find / Search text inside Entire Raw HTML\n"
        f"  [bold yellow]3[/bold yellow] - Preview First 1,500 characters",
        title="HTML Inspector",
        style="cyan",
    ))
    mode = Prompt.ask("Select mode", choices=["1", "2", "3"], default="1")
    if mode == "1":
        console.print(f"\n[bold green]--- START OF FULL RAW HTML ({len(content)} bytes) ---[/bold green]")
        console.print(content, markup=False, highlight=False)
        console.print(f"[bold green]--- END OF FULL RAW HTML ---[/bold green]\n")
    elif mode == "2":
        term = Prompt.ask("Enter search query / keyword to find entirely in HTML").strip()
        if not term:
            console.print("[yellow]Empty search term.[/yellow]")
            return
        lines = content.splitlines()
        matches = []
        for idx, line in enumerate(lines, 1):
            if term.lower() in line.lower():
                matches.append((idx, line))
        if matches:
            console.print(f"\n[bold green]Found {len(matches)} matching line(s) for '{term}':[/bold green]")
            match_table = Table(title=f"Occurrences of '{term}' in HTML")
            match_table.add_column("Line", style="cyan", justify="right")
            match_table.add_column("Matching Line Content", style="white")
            for line_no, line_text in matches:
                match_table.add_row(str(line_no), line_text.strip()[:140])
            console.print(match_table)
        else:
            console.print(f"[yellow]No occurrences found for '{term}' in raw HTML.[/yellow]")
    elif mode == "3":
        preview = content[:1500] + ("\n... [truncated for quick summary]" if len(content) > 1500 else "")
        console.print(Panel(preview, title=f"Quick Summary (First 1500 chars)", style="cyan"))


async def _op_view_downloads():
    """List downloaded pages in CAS with option to inspect HTML."""
    async with get_async_session_factory()() as session:
        page_repo = PageRepository(session)
        pages = await page_repo.list_pages(limit=None)
        if not pages:
            console.print("\n[yellow]No downloaded pages in CAS yet.[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        table = Table(title=f"All Downloaded Pages in Content Addressable Storage (CAS) ({len(pages)} Total Pages)")
        table.add_column("Page ID", style="cyan", justify="right")
        table.add_column("Status", justify="right")
        table.add_column("URL", style="white")
        table.add_column("Title", style="italic")
        table.add_column("Content SHA256", style="dim")

        for p in pages:
            url_str = getattr(p, "canonical_url", getattr(p, "url", ""))
            status_str = str(getattr(p, "http_status", getattr(p, "status_code", "-")))
            title_str = (getattr(p, "title", "-") or "-")
            table.add_row(
                str(p.id),
                status_str,
                url_str[:55] + ("..." if len(url_str) > 55 else ""),
                title_str[:30],
                (getattr(p, "latest_content_hash", None) or "-")[:16] + "...",
            )
        console.print(table)

        pid = Prompt.ask("\nEnter Page ID to inspect raw HTML entirely (or press Enter to return)", default="")
        if pid.isdigit():
            page = await page_repo.get_page(int(pid))
            if not page or not page.latest_content_hash:
                console.print("[red]Page or content hash not found.[/red]")
            else:
                storage = ContentAddressableStorage()
                content = storage.retrieve_text(page.latest_content_hash, ext="html")
                page_url = getattr(page, "canonical_url", getattr(page, "url", ""))
                if content:
                    _inspect_raw_html_interactive(content, title=f"Page {page.id} ({page_url})")
                else:
                    console.print(f"[yellow]Raw content not found on disk for hash: {page.latest_content_hash}[/yellow]")
            Prompt.ask("\nPress Enter to continue")


async def _op_run_pipeline():
    """Execute end-to-end intelligence collection pipeline."""
    async with get_async_session_factory()() as session:
        c_repo = CompanyRepository(session)
        comps = await c_repo.list_companies()
        if not comps:
            console.print("[yellow]No company registered. Please add a company first (Option 7).[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        c_table = Table(title="Select Target Company for Pipeline")
        c_table.add_column("ID", style="cyan")
        c_table.add_column("Name", style="bold white")
        c_table.add_column("Description")
        for c in comps:
            c_table.add_row(str(c.id), c.name, c.description or "")
        console.print(c_table)

        c_id = IntPrompt.ask("Enter Company ID to run pipeline", default=comps[0].id)
        max_pages = IntPrompt.ask("Max crawl pages limit", default=10)

        console.print(f"\n[bold green]Launching End-to-End Pipeline for Company ID {c_id}...[/bold green]")
        disc_worker = DiscoveryWorker()
        crawler_worker = PageFetchWorker()
        proc_worker = ProcessingWorker()

        console.print("[cyan]Step 1/3: Running discovery on surface and dark web...[/cyan]")
        await disc_worker.run_discovery_for_company(c_id)

        console.print(f"[cyan]Step 2/3: Crawling up to {max_pages} pages over Tor...[/cyan]")
        crawled = 0
        for _ in range(max_pages):
            has_job = await crawler_worker.process_one_job()
            if not has_job:
                break
            crawled += 1
            await proc_worker.process_pending_pages(limit=1)

        console.print(f"[bold green]✓ Pipeline completed! Crawled and processed {crawled} pages.[/bold green]")
        Prompt.ask("\nPress Enter to continue")


async def _op_run_crawl():
    """Drain queue and crawl pending targets."""
    max_pages = IntPrompt.ask("Enter max pages to crawl in this batch", default=10)
    crawler = PageFetchWorker()
    processor = ProcessingWorker()

    console.print(f"\n[bold cyan]Fetching up to {max_pages} pages from queue...[/bold cyan]")
    crawled = 0
    for _ in range(max_pages):
        has_job = await crawler.process_one_job()
        if not has_job:
            console.print("[yellow]Queue is now empty or no eligible jobs available.[/yellow]")
            break
        crawled += 1
        await processor.process_pending_pages(limit=1)

    console.print(f"[bold green]✓ Crawl batch finished. Processed {crawled} pages.[/bold green]")
    Prompt.ask("\nPress Enter to continue")


async def _op_run_discovery():
    """Run discovery search."""
    async with get_async_session_factory()() as session:
        c_repo = CompanyRepository(session)
        comps = await c_repo.list_companies()
        if not comps:
            console.print("[yellow]No company registered. Please add a company first.[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        c_id = IntPrompt.ask("Enter Company ID for discovery", default=comps[0].id)
        disc = DiscoveryWorker()
        console.print(f"[cyan]Executing bounded query expansion and search for Company {c_id}...[/cyan]")
        res = await disc.run_discovery_for_company(c_id)
        console.print(f"[bold green]✓ Discovered and enqueued {len(res)} new URLs.[/bold green]")
        Prompt.ask("\nPress Enter to continue")


async def _op_manage_companies():
    """List or add target companies."""
    async with get_async_session_factory()() as session:
        c_repo = CompanyRepository(session)
        comps = await c_repo.list_companies()

        table = Table(title="Target Organizations")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold white")
        table.add_column("Description")
        for c in comps:
            table.add_row(str(c.id), c.name, c.description or "")
        console.print(table)

        if Confirm.ask("\nWould you like to register a new target organization?", default=False):
            name = Prompt.ask("Enter Organization / Company Name")
            desc = Prompt.ask("Enter optional description / domain", default="")
            comp = await c_repo.create_company(name=name, description=desc)
            if desc and "." in desc:
                await c_repo.add_asset(comp.id, "domain", desc)
            await session.commit()
            console.print(f"[bold green]✓ Created target company: {comp.name} (ID: {comp.id})[/bold green]")
            Prompt.ask("\nPress Enter to continue")


async def _op_check_health():
    """Run health diagnostics."""
    console.print("\n[bold cyan]Checking system diagnostics...[/bold cyan]")
    db_ok = await check_db_health()
    proxy_mgr = get_proxy_manager()
    tor_ok = await proxy_mgr.check_tor_connectivity()
    settings = get_settings()
    cas_path = Path(settings.storage_path)
    cas_ok = cas_path.exists() and os.access(cas_path, os.W_OK)

    table = Table(title="System & Network Diagnostics")
    table.add_column("Subsystem", style="bold white")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    table.add_row(
        "Database Layer (SQLite Async)",
        "[green]ONLINE[/green]" if db_ok else "[red]OFFLINE[/red]",
        settings.database_url,
    )
    table.add_row(
        f"Tor SOCKS5 Proxy ({settings.tor_proxy_host}:{settings.tor_proxy_port})",
        "[green]ONLINE[/green]" if tor_ok else "[red]UNREACHABLE / DEGRADED[/red]",
        "Connected" if tor_ok else "Check local Tor service daemon on port 9050",
    )
    table.add_row(
        "CAS Content Storage Root",
        "[green]WRITABLE[/green]" if cas_ok else "[red]INACCESSIBLE[/red]",
        str(cas_path.absolute()),
    )
    table.add_row("Scope Policy Mode", "[cyan]ACTIVE[/cyan]", settings.scope_policy)
    console.print(table)
    Prompt.ask("\nPress Enter to continue")


async def _op_test_autoclick():
    """Test auto-click on interactive pages."""
    url = Prompt.ask("Enter target URL to test interactive auto-click", default="https://example.com")
    console.print(f"[cyan]Testing headless browser auto-click engine for {url}...[/cyan]")
    try:
        from dwi_crawler.crawling.browser import get_browser_manager
        mgr = get_browser_manager()
        res = await mgr.render_page(url, capture_screenshot=False, wait_seconds=3.0, is_onion=".onion" in url)
        if res.success:
            console.print(f"[bold green]✓ Page fetched successfully ({len(res.html)} bytes). Final URL: {res.current_url}[/bold green]")
            preview = res.html[:600] + ("\n... [truncated]" if len(res.html) > 600 else "")
            console.print(Panel(preview, title=f"Rendered Output for {url}", style="green"))
        else:
            console.print(f"[yellow]Browser rendering ended with status: {res.error or 'Failed'}[/yellow]")
    except Exception as e:
        console.print(f"[red]Auto-click test failed: {e}[/red]")
    Prompt.ask("\nPress Enter to continue")


async def run_dashboard_loop():
    """Main interactive loop for the CLI dashboard."""
    while True:
        _clear()
        try:
            data = await _fetch_telemetry()
        except Exception as e:
            console.print(f"[bold red]Failed to fetch telemetry:[/bold red] {e}")
            data = {
                "companies": 0, "urls": 0, "onion_urls": 0, "surface_urls": 0,
                "pages": 0, "links": 0, "entities": 0, "intel": 0, "findings": 0,
                "cas_mb": 0, "queue": {},
            }

        _render_header(data)
        _render_overview(data)
        console.print()
        _render_menu()

        choice = Prompt.ask("\n[bold green]DWI Dashboard[/bold green] > Select an option", default="r").strip().lower()

        if choice in ("q", "quit", "exit"):
            console.print("[cyan]Exiting DWI Dashboard. Goodbye![/cyan]")
            break
        elif choice == "1":
            await _op_view_findings()
        elif choice == "2":
            await _op_view_queue()
        elif choice == "3":
            await _op_view_downloads()
        elif choice == "4":
            await _op_run_pipeline()
        elif choice == "5":
            await _op_run_crawl()
        elif choice == "6":
            await _op_run_discovery()
        elif choice == "7":
            await _op_manage_companies()
        elif choice == "8":
            await _op_check_health()
        elif choice == "9":
            await _op_test_autoclick()
        elif choice in ("r", "refresh", ""):
            continue
        else:
            console.print(f"[yellow]Unknown option '{choice}'. Please select from 1-9, r, or q.[/yellow]")
            Prompt.ask("Press Enter to continue")



def start_dashboard():
    """Synchronous launcher entry point for typer / CLI."""
    asyncio.run(run_dashboard_loop())


if __name__ == "__main__":
    start_dashboard()
