"""CLI commands for managing companies, assets, and keywords."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from dwi_crawler.database.repositories.company_repository import CompanyRepository
from dwi_crawler.database.session import get_async_session_factory, init_db

company_app = typer.Typer(name="company", help="Manage target organizations and intelligence profiles.")
asset_app = typer.Typer(name="asset", help="Manage company digital assets and infrastructure.")
keyword_app = typer.Typer(name="keyword", help="Manage intelligence keywords and terms.")

console = Console()


# --- Company Commands ---
@company_app.command("add")
def add_company(name: str = typer.Argument(..., help="Company or target organization name"),
                description: str = typer.Option(None, "--desc", "-d", help="Optional description")):
    """Add a new company profile to DWI."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            comp = await repo.create_company(name, description)
            await session.commit()
            console.print(f"[bold green]✓[/bold green] Company created: [bold cyan]{comp.name}[/bold cyan] (ID: {comp.id})")
    asyncio.run(_run())


@company_app.command("list")
def list_companies():
    """List all configured companies in DWI."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            companies = await repo.list_companies()
            if not companies:
                console.print("[yellow]No companies registered yet. Add one using 'dwi-crawler company add'.[/yellow]")
                return

            table = Table(title="DWI Registered Target Organizations")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Company Name", style="bold white")
            table.add_column("Description", style="dim")
            table.add_column("Registered At", style="magenta")

            for c in companies:
                table.add_row(str(c.id), c.name, c.description or "", c.created_at.strftime("%Y-%m-%d %H:%M"))
            console.print(table)
    asyncio.run(_run())


@company_app.command("show")
def show_company(company_id: int = typer.Argument(..., help="Company ID")):
    """Display comprehensive details, assets, and keywords for a company."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            comp = await repo.get_by_id(company_id)
            if not comp:
                console.print(f"[bold red]Error:[/bold red] Company ID {company_id} not found.")
                return

            console.print(f"\n[bold green]═══ DWI TARGET PROFILE: {comp.name.upper()} (ID: {comp.id}) ═══[/bold green]")
            console.print(f"[bold]Description:[/bold] {comp.description or 'None'}")
            console.print(f"[bold]Created:[/bold] {comp.created_at}")

            # Assets
            console.print("\n[bold cyan]Associated Assets:[/bold cyan]")
            if comp.assets:
                a_table = Table()
                a_table.add_column("Type", style="yellow")
                a_table.add_column("Value", style="bold white")
                for a in comp.assets:
                    a_table.add_row(a.asset_type, a.value)
                console.print(a_table)
            else:
                console.print("  [dim]No assets registered.[/dim]")

            # Keywords
            console.print("\n[bold cyan]Monitoring Keywords:[/bold cyan]")
            if comp.keywords:
                k_table = Table()
                k_table.add_column("Keyword", style="bold white")
                table_cat = k_table.add_column("Category", style="green")
                k_table.add_column("Status", style="magenta")
                for k in comp.keywords:
                    status = "[green]ACTIVE[/green]" if k.is_active else "[dim]INACTIVE[/dim]"
                    k_table.add_row(k.term, k.category, status)
                console.print(k_table)
            else:
                console.print("  [dim]No keywords registered.[/dim]")
    asyncio.run(_run())


# --- Asset Commands ---
@asset_app.command("add")
def add_asset(
    company_id: int = typer.Argument(..., help="Target Company ID"),
    asset_type: str = typer.Argument(..., help="Asset type (domain, subdomain, ip, email, identity, brand)"),
    value: str = typer.Argument(..., help="Asset value (e.g., acme.com, 1.2.3.4, ceo@acme.com)"),
):
    """Add a digital asset to a company profile."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            comp = await repo.get_by_id(company_id)
            if not comp:
                console.print(f"[bold red]Error:[/bold red] Company ID {company_id} not found.")
                return
            asset = await repo.add_asset(company_id, asset_type, value)
            await session.commit()
            console.print(f"[bold green]✓[/bold green] Asset added to {comp.name}: [bold yellow]{asset.asset_type}[/bold yellow] -> {asset.value}")
    asyncio.run(_run())


@asset_app.command("list")
def list_assets(company_id: int = typer.Argument(..., help="Target Company ID")):
    """List assets associated with a company."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            comp = await repo.get_by_id(company_id)
            if not comp:
                console.print(f"[bold red]Error:[/bold red] Company ID {company_id} not found.")
                return

            assets = await repo.list_assets(company_id)
            table = Table(title=f"Assets for {comp.name}")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Value", style="bold white")
            table.add_column("Added At", style="dim")
            for a in assets:
                table.add_row(str(a.id), a.asset_type, a.value, a.created_at.strftime("%Y-%m-%d %H:%M"))
            console.print(table)
    asyncio.run(_run())


# --- Keyword Commands ---
@keyword_app.command("add")
def add_keyword(
    company_id: int = typer.Argument(..., help="Target Company ID"),
    term: str = typer.Argument(..., help="Search keyword or phrase to monitor"),
    category: str = typer.Option("general", "--category", "-c", help="Category (brand, executive, product, infrastructure)"),
):
    """Add an intelligence monitoring keyword to a company."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            comp = await repo.get_by_id(company_id)
            if not comp:
                console.print(f"[bold red]Error:[/bold red] Company ID {company_id} not found.")
                return
            kw = await repo.add_keyword(company_id, term, category)
            await session.commit()
            console.print(f"[bold green]✓[/bold green] Keyword added to {comp.name}: '[bold white]{kw.term}[/bold white]' ({kw.category})")
    asyncio.run(_run())


@keyword_app.command("list")
def list_keywords(company_id: int = typer.Argument(..., help="Target Company ID")):
    """List all keywords monitored for a company."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            repo = CompanyRepository(session)
            comp = await repo.get_by_id(company_id)
            if not comp:
                console.print(f"[bold red]Error:[/bold red] Company ID {company_id} not found.")
                return
            keywords = await repo.list_keywords(company_id)
            table = Table(title=f"Monitoring Keywords for {comp.name}")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Keyword", style="bold white")
            table.add_column("Category", style="green")
            table.add_column("Status", style="magenta")
            for k in keywords:
                st = "[green]ACTIVE[/green]" if k.is_active else "[dim]INACTIVE[/dim]"
                table.add_row(str(k.id), k.term, k.category, st)
            console.print(table)
    asyncio.run(_run())


@keyword_app.command("enhance")
def enhance_keyword(
    term: str = typer.Argument(..., help="Raw keyword to enhance"),
    company: str = typer.Option("", "--company", "-c", help="Optional company name"),
    domain: str = typer.Option("", "--domain", "-d", help="Optional company domain"),
):
    """Inspect the generated bounded search permutations for a keyword."""
    from dwi_crawler.discovery.enhancer import KeywordEnhancer
    qs = KeywordEnhancer.enhance_keyword(term, company_name=company, domain=domain)

    console.print(f"\n[bold green]═══ KEYWORD ENHANCEMENT: '{term}' ═══[/bold green]")
    console.print(f"[dim]Company: {company or 'N/A'}, Domain: {domain or 'N/A'}[/dim]\n")

    s_table = Table(title="Surface Web Discovery Queries (Limit: 3)")
    s_table.add_column("#", style="cyan", justify="right")
    s_table.add_column("Search Query", style="bold white")
    for i, q in enumerate(qs.surface_queries, 1):
        s_table.add_row(str(i), q)
    console.print(s_table)

    o_table = Table(title="Onion Service Discovery Queries (Limit: 7)")
    o_table.add_column("#", style="cyan", justify="right")
    o_table.add_column("Search Query", style="bold yellow")
    for i, q in enumerate(qs.onion_queries, 1):
        o_table.add_row(str(i), q)
    console.print(o_table)
    console.print("[dim]Total bounded queries generated: 10 searches.[/dim]\n")
