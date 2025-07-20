"""
Command-line interface for Netflix OCA Locator.

This module provides a rich, interactive CLI using Typer and Rich.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config.settings import Settings, get_settings
from ..core.models import ExportFormat, OCALocatorResult
from ..core.oca_locator import create_locator
from ..utils.formatters import ResultFormatter
from ..utils.mapping import MapGenerator

# Initialize Rich console
console = Console()

# Create Typer app
app = typer.Typer(
    name="netflix-oca-locator",
    help="🌐 Locate Netflix Open Connect Appliances (OCAs) for your network",
    add_completion=True,
    rich_markup_mode="rich",
)


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging based on debug flag.

    Parameters
    ----------
    debug : bool
        Enable debug logging.
    """
    # Remove default logger
    logger.remove()

    # Add console logger
    if debug:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
        )
    else:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
            level="INFO",
        )


def print_banner() -> None:
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║         🌐 Netflix OCA Locator v2.0.0 🌐                  ║
    ║                                                           ║
    ║  Discover Netflix's Open Connect Appliances serving       ║
    ║  your network for optimal streaming performance           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


@app.command()
def main(
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Export format: json, csv, xlsx, markdown",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "-f",
        help="Output file path",
    ),
    map: bool = typer.Option(
        False,
        "--map",
        "-m",
        help="Generate interactive map of OCA locations",
    ),
    open_map: bool = typer.Option(
        False,
        "--open-map",
        help="Open generated map in browser",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
    no_emoji: bool = typer.Option(
        False,
        "--no-emoji",
        help="Disable emoji in output",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Minimal output (only show results)",
    ),
) -> None:
    """
    Locate Netflix OCAs for your network.

    This command will:
    - Detect your public IP address
    - Identify your ISP information
    - Find Netflix OCA servers allocated to your network
    - Display detailed information about each OCA
    - Optionally export results or generate maps
    """
    # Setup
    setup_logging(debug)
    settings = get_settings()
    settings.show_emoji = not no_emoji

    if not quiet:
        print_banner()

    # Run the async main function
    try:
        result = asyncio.run(locate_ocas_async(settings, quiet))

        # Display results
        if not quiet:
            display_results(result, settings)
        else:
            display_minimal_results(result)

        # Handle exports
        if output:
            export_results(result, output, output_file)

        # Handle map generation
        if map or open_map:
            generate_map(result, open_map)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


async def locate_ocas_async(settings: Settings, quiet: bool) -> OCALocatorResult:
    """
    Asynchronously locate OCAs with progress indication.

    Parameters
    ----------
    settings : Settings
        Application settings.
    quiet : bool
        Whether to suppress progress output.

    Returns
    -------
    OCALocatorResult
        Complete OCA location result.
    """
    locator = await create_locator()

    if quiet:
        return await locator.locate_ocas()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Locating Netflix OCAs...", total=None)

        # Update progress messages during execution
        async def run_with_progress():
            progress.update(task, description="📍 Fetching public IP address...")
            await asyncio.sleep(0.1)  # Allow UI update

            result = await locator.locate_ocas()

            progress.update(task, description="✅ Complete!")
            return result

        return await run_with_progress()


def display_results(result: OCALocatorResult, settings: Settings) -> None:
    """
    Display results in a rich format.

    Parameters
    ----------
    result : OCALocatorResult
        OCA location results.
    settings : Settings
        Application settings.
    """
    emoji = "🌐 " if settings.show_emoji else ""

    # Display user info
    user_info = Panel(
        f"[bold]Public IP:[/bold] {result.public_ip.ip}\n"
        f"[bold]ISP:[/bold] {result.isp_info.as_name}\n"
        f"[bold]AS Number:[/bold] AS{result.isp_info.asn}\n"
        f"[bold]Country:[/bold] {result.isp_info.cc}\n"
        f"[bold]BGP Prefix:[/bold] {result.isp_info.bgp_prefix}",
        title=f"{emoji}Your Network Information",
        border_style="cyan",
    )
    console.print(user_info)

    # Display OCA servers
    if result.oca_servers:
        table = Table(
            title=f"\n{emoji}Netflix OCA Servers Allocated to Your Network",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
        )

        table.add_column("Domain", style="cyan", no_wrap=True)
        table.add_column("IP Address", style="green")
        table.add_column("Location", style="yellow")
        table.add_column("IATA", style="blue")
        table.add_column("ASN", style="magenta")
        table.add_column("Provider", style="dim")
        table.add_column("Method", style="bright_black")

        for oca in result.oca_servers:
            location = oca.city or "Unknown"
            if settings.show_emoji and oca.city:
                location = f"📍 {location}"

            table.add_row(
                oca.domain,
                str(oca.ip_address),
                location,
                oca.iata_code or "-",
                oca.asn or "-",
                oca.geocoding_provider or "-",
                oca.geolocation_approach or "-",
            )

        console.print(table)
        console.print(
            f"\n[green]Found {len(result.oca_servers)} OCA server(s)[/green]"
        )
    else:
        console.print("\n[yellow]No OCA servers found[/yellow]")


def display_minimal_results(result: OCALocatorResult) -> None:
    """
    Display minimal results for quiet mode.

    Parameters
    ----------
    result : OCALocatorResult
        OCA location results.
    """
    for oca in result.oca_servers:
        console.print(f"{oca.domain} {oca.ip_address}")


def export_results(
    result: OCALocatorResult,
    format_type: str,
    output_file: Path | None,
) -> None:
    """
    Export results to file.

    Parameters
    ----------
    result : OCALocatorResult
        Results to export.
    format_type : str
        Export format.
    output_file : Optional[Path]
        Output file path.
    """
    try:
        formatter = ResultFormatter(get_settings())
        ExportFormat(format=format_type.lower())

        # Determine output path
        if output_file is None:
            output_file = Path(f"oca_results.{format_type.lower()}")

        # Export based on format
        if format_type.lower() == "json":
            formatter.export_json(result, output_file)
        elif format_type.lower() == "csv":
            formatter.export_csv(result, output_file)
        elif format_type.lower() == "xlsx":
            formatter.export_excel(result, output_file)
        elif format_type.lower() == "markdown":
            formatter.export_markdown(result, output_file)
        else:
            console.print(f"[red]Unsupported format: {format_type}[/red]")
            return

        console.print(f"[green]✅ Results exported to {output_file}[/green]")

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")


def generate_map(result: OCALocatorResult, open_browser: bool) -> None:
    """
    Generate interactive map.

    Parameters
    ----------
    result : OCALocatorResult
        Results to map.
    open_browser : bool
        Whether to open map in browser.
    """
    try:
        map_gen = MapGenerator(get_settings())
        map_path = map_gen.create_oca_map(result)

        console.print(f"[green]✅ Map generated: {map_path}[/green]")

        if open_browser:
            import webbrowser
            webbrowser.open(f"file://{map_path.absolute()}")
            console.print("[green]📍 Map opened in browser[/green]")

    except Exception as e:
        console.print(f"[red]Map generation failed: {e}[/red]")


@app.command()
def version() -> None:
    """Show version information."""
    from .. import __version__

    console.print(f"Netflix OCA Locator v{__version__}")


@app.command()
def info() -> None:
    """Show detailed application information."""
    from .. import __author__, __version__

    info_panel = Panel(
        f"[bold]Netflix OCA Locator[/bold]\n\n"
        f"Version: {__version__}\n"
        f"Author: {__author__}\n"
        f"License: MIT\n\n"
        f"This tool helps you discover Netflix's Open Connect Appliances (OCAs) "
        f"that are allocated to serve content to your network, providing insights "
        f"into Netflix's content delivery infrastructure.",
        title="📦 Application Information",
        border_style="blue",
    )
    console.print(info_panel)


if __name__ == "__main__":
    app()
