"""Main entry point for the DWI Dark Web and Onion Intelligence Crawler CLI."""

import typer
from dwi_crawler.cli.captcha import captcha_app
from dwi_crawler.cli.company import asset_app, company_app, keyword_app
from dwi_crawler.cli.crawl import crawl_cli, execute_crawl, run_pipeline
from dwi_crawler.cli.dashboard import start_dashboard
from dwi_crawler.cli.queue import queue_app
from dwi_crawler.cli.search import run_discover, run_search, search_cli
from dwi_crawler.cli.stats import (
    check_health,
    download_app,
    links_app,
    result_app,
    show_config,
    show_stats,
    stats_cli,
)
from dwi_crawler.cli.workers import workers_app

app = typer.Typer(
    name="dwi-crawler",
    help="DWI Dark Web and Onion Intelligence Crawler - High-assurance intelligence collection CLI.",
    add_completion=False,
    no_args_is_help=True,
)

# Register Sub-Command Groups
app.add_typer(company_app, name="company")
app.add_typer(asset_app, name="asset")
app.add_typer(keyword_app, name="keyword")
app.add_typer(queue_app, name="queue")
app.add_typer(workers_app, name="workers")
app.add_typer(captcha_app, name="captcha")
app.add_typer(result_app, name="result")
app.add_typer(links_app, name="links")
app.add_typer(download_app, name="download")

# Register Direct Root Commands
app.command("search", help="Execute dark web and surface web discovery searches.")(run_search)
app.command("discover", help="Trigger discovery search pipeline for target companies.")(run_discover)
app.command("crawl", help="Drain crawl queue and fetch target pages through Tor.")(execute_crawl)
app.command("run", help="Run complete end-to-end intelligence collection pipeline.")(run_pipeline)
app.command("stats", help="Display system, storage, and intelligence telemetry.")(show_stats)
app.command("health", help="Diagnose Tor proxy, database, and storage health.")(check_health)
app.command("config", help="Inspect runtime configuration.")(show_config)
app.command("dashboard", help="Launch interactive CLI menu dashboard.")(start_dashboard)

# Multi-Company Dark Web Verification
from check_companies import check_companies
app.command("check", help="Verify and check dark web intelligence for both companies (Tolaram & MetaYB).")(check_companies)


def main():
    app()


if __name__ == "__main__":
    main()
