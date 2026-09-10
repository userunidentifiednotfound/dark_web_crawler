"""CLI commands for human-assisted CAPTCHA solving."""

import asyncio
from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select, update
from dwi_crawler.crawling.browser import get_browser_manager
from dwi_crawler.database.session import get_async_session_factory, init_db
from dwi_crawler.models.job import CaptchaEvent, CrawlJob

captcha_app = typer.Typer(name="captcha", help="Human-assisted CAPTCHA queue and manual challenge resolution.")
console = Console()


@captcha_app.command("list")
def list_captchas():
    """List pending CAPTCHA challenges requiring human assistance."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            stmt = select(CaptchaEvent).where(CaptchaEvent.status == "WAITING").order_by(CaptchaEvent.detected_at.desc())
            res = await session.execute(stmt)
            events = list(res.scalars().all())

            if not events:
                console.print("[bold green]✓ No active CAPTCHA challenges waiting in queue.[/bold green]")
                return

            table = Table(title="CAPTCHA Challenges Pending Analyst Resolution")
            table.add_column("Event ID", style="cyan", justify="right")
            table.add_column("Job ID", style="magenta")
            table.add_column("Target URL", style="bold yellow")
            table.add_column("Challenge Type", style="red")
            table.add_column("Detected At", style="dim")

            for ev in events:
                table.add_row(
                    str(ev.id),
                    str(ev.job_id or "N/A"),
                    ev.url,
                    ev.captcha_type,
                    ev.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
                )
            console.print(table)
            console.print("\n[dim]To solve a challenge manually, run:[/dim] [bold cyan]dwi-crawler captcha solve <job-id>[/bold cyan]\n")
    asyncio.run(_run())


@captcha_app.command("solve")
def solve_captcha(job_id: int = typer.Argument(..., help="Crawl Job ID with CAPTCHA challenge")):
    """Open a controlled browser session for an authorized analyst to manually solve the CAPTCHA."""
    async def _run():
        await init_db()
        async with get_async_session_factory()() as session:
            stmt = select(CrawlJob).where(CrawlJob.id == job_id)
            res = await session.execute(stmt)
            job = res.scalar_one_or_none()
            if not job:
                console.print(f"[bold red]Error:[/bold red] Job ID {job_id} not found.")
                return

            console.print(f"[bold yellow]Initiating controlled analyst session for:[/bold yellow] {job.url}")
            browser_mgr = get_browser_manager()
            success = await browser_mgr.launch_human_assisted_session(job.url)

            if success:
                # Mark captcha event resolved
                now = datetime.utcnow()
                c_stmt = (
                    update(CaptchaEvent)
                    .where(CaptchaEvent.job_id == job.id, CaptchaEvent.status == "WAITING")
                    .values(status="HUMAN_RESOLVED", resolved_at=now, resolved_by="analyst-cli")
                )
                await session.execute(c_stmt)

                # Requeue job to PENDING so page fetch worker can resume capture
                job.status = "PENDING"
                job.error_message = None
                job.next_run_at = now
                await session.commit()
                console.print(f"[bold green]✓ Challenge completed. Job {job.job_id[:8]} requeued for immediate capture.[/bold green]")
            else:
                console.print(f"[bold red]Failed to resolve challenge for job {job_id}.[/bold red]")
    asyncio.run(_run())
