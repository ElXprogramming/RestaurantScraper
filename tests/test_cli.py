from typer.testing import CliRunner
from scraper.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "RestaurantScraper" in result.output
    assert "scrape" in result.output
    assert "export" in result.output
    assert "db" in result.output
    assert "ui" in result.output


def test_cli_stats():
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "Total Restaurants" in result.output
    assert "Total Menu Items" in result.output


def test_cli_db_list():
    result = runner.invoke(app, ["db", "list", "--limit", "5"])
    assert result.exit_code == 0
    assert "Restaurants in Database" in result.output


def test_cli_db_view():
    result = runner.invoke(app, ["db", "view", "After 10 Cafe"])
    assert result.exit_code == 0
    assert "Restaurant Details" in result.output
    assert "After 10 Cafe" in result.output


def test_cli_export(tmp_path):
    result = runner.invoke(app, ["export", "--out-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "menu_items.csv").exists()
    assert (tmp_path / "restaurants.json").exists()


def test_cli_export_selected(tmp_path):
    result = runner.invoke(app, ["export", "--ids", "24", "--out-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Exporting 1 selected restaurant" in result.output
    assert (tmp_path / "menu_items.csv").exists()
    assert (tmp_path / "restaurants.json").exists()

