"""RestaurantScraper CLI: Modern, local-first restaurant & menu scraper engine using Typer and Rich."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import typer

from scraper import config, db, discovery
from scraper.extract_website import scrape_website
from scraper.http_client import PoliteClient
from scraper.runner import cmd_scrape as run_scrape

__version__ = "0.2.0"

app = typer.Typer(
    name="restaurantscraper",
    help="🍽️ RestaurantScraper: High-performance restaurant menu scraper, organized database explorer, and export tool.",
    add_completion=False,
    no_args_is_help=True,
)

db_app = typer.Typer(
    name="db",
    help="📂 Inspect, query, and manage the local restaurant & menu SQLite database.",
    add_completion=False,
    no_args_is_help=True,
)
app.add_typer(db_app, name="db")

console = Console()


def _print_banner() -> None:
    """Print the stylized RestaurantScraper banner."""
    banner_text = (
        f"[bold cyan]RestaurantScraper[/bold cyan] [dim]v{__version__}[/dim]\n"
        "[dim]Local-first • Menu Extraction • Organized Database • CSV/JSON Export[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


@app.command("ui")
def cmd_ui(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host address."),
    port: int = typer.Option(8765, "--port", "-p", help="Server port."),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Do not automatically open the default web browser."
    ),
) -> None:
    """Launch the RestaurantScraper Local Interactive Web GUI Dashboard."""
    _print_banner()
    console.print(
        f"[bold green]🚀 Starting Local Web GUI at:[/bold green] [cyan]http://{host}:{port}[/cyan]"
    )
    console.print("[dim]Press Ctrl+C to stop the GUI server.[/dim]\n")
    from scraper.server import start_server

    start_server(
        host=host,
        port=port,
        open_browser=not no_browser,
    )


@app.command("gui", hidden=True)
def cmd_gui(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host address."),
    port: int = typer.Option(8765, "--port", "-p", help="Server port."),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Do not automatically open the default web browser."
    ),
) -> None:
    """Alias for ui command."""
    cmd_ui(host=host, port=port, no_browser=no_browser)


@app.command("scrape")
def cmd_scrape_url(
    url: str = typer.Argument(..., help="GrabFood, Foodpanda, or website URL to scrape"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Optional override for restaurant name"),
    render: bool = typer.Option(False, "--render", "-r", help="Use headless Playwright browser (JS-heavy sites)"),
    area: Optional[str] = typer.Option(None, "--area", "-a", help="Area override (e.g. 1borneo, alamesra)"),
    cuisine: Optional[str] = typer.Option(None, "--cuisine", "-c", help="Cuisine tags"),
) -> None:
    """Scrape menu items and details from a URL (GrabFood, Foodpanda, or website)."""
    _print_banner()
    console.print(f"[bold cyan]Target URL:[/bold cyan] {url}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Scraping target menu and parsing data...", total=None)
        res = run_scrape(
            url=url,
            name=name,
            area=area,
            cuisine=cuisine,
            render=render,
            save_sqlite=True,
        )

    if not res.get("success"):
        console.print(f"[bold red]❌ Scraping failed:[/bold red] {res.get('error', 'Unknown error')}")
        raise typer.Exit(1)

    rest_name = res.get("restaurantName", "Unknown")
    items = res.get("items", [])
    merged = res.get("isMerged", False)
    rid = res.get("restaurantId")

    console.print(f"[bold green]✓ Successfully scraped:[/bold green] [bold white]{rest_name}[/bold white] (ID: {rid})")
    if merged:
        console.print("[dim yellow]ℹ Merged and updated existing restaurant record.[/dim yellow]")
    else:
        console.print("[dim green]ℹ Created new restaurant entry in database.[/dim green]")

    console.print(f"• [bold cyan]Extracted Items:[/bold cyan] {len(items)}")
    if res.get("cuisine"):
        console.print(f"• [bold cyan]Cuisine:[/bold cyan] {res['cuisine']}")
    if res.get("rating"):
        console.print(f"• [bold cyan]Rating:[/bold cyan] ⭐ {res['rating']}")
    if res.get("address"):
        console.print(f"• [bold cyan]Address:[/bold cyan] {res['address']}")

    if items:
        table = Table(title=f"Sample Items from {rest_name}", box=box.ROUNDED)
        table.add_column("Category", style="cyan")
        table.add_column("Item Name", style="bold white")
        table.add_column("Price (MYR)", justify="right", style="green")
        table.add_column("Description", style="dim")

        for item in items[:15]:
            table.add_row(
                item.get("category", "General"),
                item.get("name", ""),
                f"RM {item.get('price', 0.0):.2f}",
                (item.get("description") or "")[:40],
            )
        console.print(table)
        if len(items) > 15:
            console.print(f"[dim]... and {len(items) - 15} more items saved to database.[/dim]")


@app.command("discover")
def cmd_discover_places(
    source: str = typer.Option("all", "--source", "-s", help="Source: osm, google, or all"),
    radius: int = typer.Option(config.DEFAULT_RADIUS_M, "--radius", "-r", help="Radius in metres"),
) -> None:
    """Discover restaurants around 1Borneo / Alamesra (OpenStreetMap / Google Places)."""
    _print_banner()
    conn = db.connect(config.DB_PATH)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        if source in ("osm", "all"):
            task = progress.add_task("Querying OpenStreetMap Overpass API...", total=None)
            n_osm = discovery.discover_osm(conn, radius)
            console.print(f"[bold green]✓ OSM:[/bold green] {n_osm} places discovered")

        if source in ("google", "all"):
            try:
                task = progress.add_task("Querying Google Places API...", total=None)
                n_google = discovery.discover_google(conn, radius)
                console.print(f"[bold green]✓ Google Places:[/bold green] {n_google} places discovered")
            except RuntimeError as e:
                console.print(f"[yellow]Google Places skipped:[/yellow] {e}")

    total_in_db = conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
    console.print(f"\n[bold green]Total Restaurants in Database:[/bold green] {total_in_db}")


@app.command("delivery")
def cmd_delivery_batch(
    only: Optional[str] = typer.Option(None, "--only", help="Filter restaurants containing text"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max restaurants to scrape"),
) -> None:
    """Batch scrape delivery links (GrabFood / foodpanda) saved in the database."""
    _print_banner()
    from scraper.extract_delivery import scrape_delivery

    conn = db.connect(config.DB_PATH)
    targets = []
    for col, label in (("grab_url", "grabfood"), ("foodpanda_url", "foodpanda")):
        q = f"SELECT * FROM restaurants WHERE {col} IS NOT NULL AND {col}!=''"
        args = []
        if only:
            q += " AND name LIKE ?"
            args.append(f"%{only}%")
        q += " ORDER BY name" + (f" LIMIT {int(limit)}" if limit else "")
        rows = conn.execute(q, args).fetchall()
        for r in rows:
            targets.append((r, col, label))

    if not targets:
        console.print("[yellow]No delivery platform URLs found matching criteria.[/yellow]")
        return

    console.print(f"[bold cyan]Found {len(targets)} delivery targets to process.[/bold cyan]\n")

    for r, col, label in targets:
        console.print(f"[{r['id']}] [bold white]{r['name']}[/bold white] ({label})")
        try:
            items = scrape_delivery(r[col])
        except Exception as e:
            db.log(conn, r["id"], label, "error", str(e))
            console.print(f"    [red]failed: {e}[/red]")
            continue
        n = db.replace_menu_items(conn, r["id"], label, r[col], items) if items else 0
        db.log(conn, r["id"], label, "ok" if n else "empty", f"{n} items")
        console.print(f"    [green]-> {n} items saved[/green]")


@app.command("add-link")
def cmd_add_link(
    name: str = typer.Argument(..., help="Restaurant name"),
    url: str = typer.Argument(..., help="Website or GrabFood/Foodpanda URL"),
) -> None:
    """Attach a Website, GrabFood, or Foodpanda URL to a restaurant in the database."""
    conn = db.connect(config.DB_PATH)
    col = (
        "grab_url" if "grab.com" in url
        else "foodpanda_url" if "foodpanda" in url
        else "website"
    )
    rows = conn.execute("SELECT id, name FROM restaurants WHERE name LIKE ?", (f"%{name}%",)).fetchall()
    if len(rows) > 1:
        console.print(f"[bold red]Multiple restaurants match '{name}':[/bold red] {[r['name'] for r in rows]}")
        raise typer.Exit(1)
    if len(rows) == 0:
        area = (
            "alamesra" if "alamesra" in name.lower() or "alamesra" in url.lower()
            else "1borneo" if "borneo" in name.lower() or "borneo" in url.lower()
            else None
        )
        rid = db.upsert_restaurant(conn, {"name": name, col: url, "area": area})
        console.print(f"[bold green]✓ Created new restaurant:[/bold green] '{name}' (ID {rid}) with {col}")
    else:
        conn.execute(f"UPDATE restaurants SET {col}=? WHERE id=?", (url, rows[0]["id"]))
        conn.commit()
        console.print(f"[bold green]✓ Updated {col} for:[/bold green] '{rows[0]['name']}'")


@app.command("export")
def cmd_export(
    out_dir: Path = typer.Option(config.EXPORT_DIR, "--out-dir", "-o", help="Target export folder"),
    format: str = typer.Option("all", "--format", "-f", help="Export format: csv, json, or all"),
    ids: Optional[str] = typer.Option(None, "--ids", "-i", help="Comma-separated restaurant IDs to export (e.g. 24,19)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter by restaurant name substring"),
    area: Optional[str] = typer.Option(None, "--area", "-a", help="Filter by area (e.g. 1borneo, alamesra)"),
) -> None:
    """Export the database to CSV and/or JSON datasets (supports exporting selected restaurants)."""
    _print_banner()
    conn = db.connect(config.DB_PATH)

    selected_ids = []
    if ids:
        for part in ids.split(","):
            part = part.strip()
            if part.isdigit():
                selected_ids.append(int(part))
    elif name or area:
        query = "SELECT id FROM restaurants WHERE 1=1"
        params = []
        if name:
            query += " AND LOWER(name) LIKE ?"
            params.append(f"%{name.strip().lower()}%")
        if area:
            query += " AND LOWER(COALESCE(area, '')) = ?"
            params.append(area.strip().lower())
        rows = conn.execute(query, params).fetchall()
        selected_ids = [r["id"] for r in rows]
        if not selected_ids:
            console.print("[yellow]No restaurants match the specified selection filter.[/yellow]")
            return

    if selected_ids:
        console.print(f"[bold cyan]Exporting {len(selected_ids)} selected restaurant(s):[/bold cyan] IDs {selected_ids}")
    else:
        console.print("[bold cyan]Exporting all restaurants in database.[/bold cyan]")

    res = db.export(conn, out_dir, restaurant_ids=selected_ids if selected_ids else None)

    table = Table(title="Dataset Export Summary", box=box.ROUNDED)
    table.add_column("Artifact", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Output Path", style="dim")

    table.add_row("Menu Items (CSV)", str(res["menu_items"]), res["csv_path"])
    table.add_row("Restaurants (JSON)", str(res["restaurants"]), res["json_path"])
    console.print(table)
    console.print(f"[bold green]✓ Export files generated successfully in:[/bold green] {out_dir}")


@app.command("stats")
def cmd_stats() -> None:
    """Show quick coverage statistics summary."""
    cmd_db_stats()


# --- DB Sub-commands ---

@db_app.command("list")
def cmd_db_list(
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search name, cuisine, address, or item"),
    area: Optional[str] = typer.Option(None, "--area", "-a", help="Filter by area (e.g. 1borneo, alamesra)"),
    cuisine: Optional[str] = typer.Option(None, "--cuisine", "-c", help="Filter by cuisine"),
    has_menu: Optional[bool] = typer.Option(None, "--has-menu/--no-menu", help="Filter by menu presence"),
    sort: str = typer.Option("name", "--sort", help="Sort by: name, rating, items, updated, price"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of records to show"),
) -> None:
    """View organized list of restaurants with menu stats."""
    _print_banner()
    conn = db.connect(config.DB_PATH)
    rows = db.get_restaurants_organized(
        conn,
        search=search,
        area=area,
        cuisine=cuisine,
        has_menu=has_menu,
        sort_by=sort,
        limit=limit,
    )

    if not rows:
        console.print("[yellow]No restaurants match the specified criteria.[/yellow]")
        return

    table = Table(title=f"Restaurants in Database ({len(rows)} shown)", box=box.ROUNDED)
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Name", style="bold white")
    table.add_column("Area", style="cyan")
    table.add_column("Cuisine", style="magenta")
    table.add_column("Rating", justify="center", style="yellow")
    table.add_column("Items", justify="right", style="green")
    table.add_column("Avg Price", justify="right", style="bold green")
    table.add_column("Sources", style="dim")

    for r in rows:
        rating_str = f"⭐ {r['rating']:.1f}" if r.get("rating") else "-"
        avg_str = f"RM {r['avg_price']:.2f}" if r.get("avg_price") else "-"
        sources_str = ", ".join(r.get("sources", [])) or "-"
        table.add_row(
            str(r["id"]),
            r["name"],
            r.get("area") or "-",
            r.get("cuisine") or "-",
            rating_str,
            str(r["items_count"]),
            avg_str,
            sources_str,
        )

    console.print(table)
    console.print(f"[dim]Use [bold cyan]restaurantscraper db view <ID>[/bold cyan] to inspect full menu items.[/dim]")


@db_app.command("view")
def cmd_db_view(
    identifier: str = typer.Argument(..., help="Restaurant ID or Name"),
) -> None:
    """Inspect detailed information and organized menu items for a restaurant."""
    _print_banner()
    conn = db.connect(config.DB_PATH)
    rest = db.get_restaurant_detail(conn, identifier)

    if not rest:
        console.print(f"[bold red]Restaurant not found for identifier:[/bold red] '{identifier}'")
        raise typer.Exit(1)

    details = (
        f"[bold white]{rest['name']}[/bold white] (ID: {rest['id']})\n"
        f"• [cyan]Area:[/cyan] {rest.get('area') or 'Unspecified'}\n"
        f"• [cyan]Cuisine:[/cyan] {rest.get('cuisine') or 'N/A'}\n"
        f"• [cyan]Rating:[/cyan] {'⭐ ' + str(rest['rating']) if rest.get('rating') else 'No rating'}\n"
        f"• [cyan]Address:[/cyan] {rest.get('address') or 'N/A'}\n"
        f"• [cyan]Hours:[/cyan] {rest.get('opening_hours') or 'N/A'}\n"
        f"• [cyan]GrabFood:[/cyan] {rest.get('grab_url') or '-'}\n"
        f"• [cyan]Website:[/cyan] {rest.get('website') or '-'}\n"
        f"• [cyan]Menu Summary:[/cyan] {rest['items_count']} items across {rest['categories_count']} categories"
        + (f" (Avg: RM {rest['avg_price']:.2f}, Range: RM {rest['min_price']:.2f} - RM {rest['max_price']:.2f})" if rest['avg_price'] else "")
    )
    console.print(Panel(details, title="Restaurant Details", border_style="cyan"))

    categories = rest.get("categories", {})
    if not categories:
        console.print("[yellow]No menu items recorded for this restaurant.[/yellow]")
        return

    for cat_name, cat_items in categories.items():
        cat_table = Table(title=f"Category: {cat_name} ({len(cat_items)} items)", box=box.SIMPLE_HEAVY)
        cat_table.add_column("Item Name", style="bold white")
        cat_table.add_column("Price (MYR)", justify="right", style="green")
        cat_table.add_column("Description", style="dim")
        cat_table.add_column("Source", style="dim cyan")

        for it in cat_items:
            cat_table.add_row(
                it.get("name", ""),
                f"RM {it.get('price', 0.0):.2f}" if it.get("price") is not None else "-",
                (it.get("description") or "")[:50],
                it.get("source", "-"),
            )
        console.print(cat_table)


@db_app.command("stats")
def cmd_db_stats() -> None:
    """View comprehensive database and menu coverage statistics."""
    _print_banner()
    conn = db.connect(config.DB_PATH)
    s = db.get_database_stats(conn)

    overview = (
        f"• [bold cyan]Total Restaurants:[/bold cyan] {s['total_restaurants']}\n"
        f"• [bold green]Total Menu Items:[/bold green] {s['total_menu_items']}\n"
        f"• [bold cyan]Restaurants with Menu:[/bold cyan] {s['restaurants_with_menu']} ({(s['restaurants_with_menu'] / max(1, s['total_restaurants'])) * 100:.1f}%)\n"
        f"• [bold cyan]With Website:[/bold cyan] {s['restaurants_with_website']}\n"
        f"• [bold cyan]With GrabFood URL:[/bold cyan] {s['restaurants_with_grab']}\n"
        f"• [bold cyan]With foodpanda URL:[/bold cyan] {s['restaurants_with_foodpanda']}\n"
        f"• [bold green]Price Range:[/bold green] RM {s['price_stats']['min']:.2f} - RM {s['price_stats']['max']:.2f} (Avg: RM {s['price_stats']['avg']:.2f})"
    )
    console.print(Panel(overview, title="Database Coverage Overview", border_style="cyan"))

    # Area Breakdown
    if s.get("areas"):
        area_table = Table(title="Area Breakdown", box=box.ROUNDED)
        area_table.add_column("Area", style="cyan")
        area_table.add_column("Restaurants Count", justify="right", style="green")
        for a, cnt in s["areas"].items():
            area_table.add_row(a, str(cnt))
        console.print(area_table)

    # Source Breakdown
    if s.get("sources"):
        source_table = Table(title="Menu Items by Source", box=box.ROUNDED)
        source_table.add_column("Source", style="cyan")
        source_table.add_column("Menu Items Count", justify="right", style="green")
        for src, cnt in s["sources"].items():
            source_table.add_row(src, str(cnt))
        console.print(source_table)


@db_app.command("delete")
def cmd_db_delete(
    restaurant_id: int = typer.Argument(..., help="ID of restaurant to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete without confirmation prompt"),
) -> None:
    """Delete a restaurant and its menu items from the database."""
    conn = db.connect(config.DB_PATH)
    row = conn.execute("SELECT id, name FROM restaurants WHERE id=?", (restaurant_id,)).fetchone()
    if not row:
        console.print(f"[bold red]Restaurant ID {restaurant_id} not found.[/bold red]")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to permanently delete '{row['name']}' (ID {row['id']}) and all its items?")
        if not confirm:
            console.print("[dim]Aborted.[/dim]")
            return

    db.delete_restaurant(conn, restaurant_id)
    console.print(f"[bold green]✓ Deleted restaurant '{row['name']}' (ID {restaurant_id})[/bold green]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
