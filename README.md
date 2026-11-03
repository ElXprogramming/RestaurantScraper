# 🍽️ RestaurantScraper

**Modern, local-first restaurant & menu scraper engine, organized SQLite database explorer, and export tool.**

Built with Python, Typer, Rich, Playwright Chromium, and an embedded zero-dependency local Web GUI. Exactly modeled after modern local-first productivity tools: fast at the CLI and beautiful in the browser.

---

## ⚡ The Three Core Capabilities

| Capability | CLI Command | Local GUI Dashboard |
|---|---|---|
| **1. Scraper Function** | `restaurantscraper scrape <URL>` | **Scraper Studio**: paste GrabFood, foodpanda, or website URL, view live extraction logs, preview items. |
| **2. Database Explorer** | `restaurantscraper db list` / `db view <ID>` | **Database Explorer**: filter by area/cuisine, instant search, click to view categorized menus with prices. |
| **3. Export Function** | `restaurantscraper export` | **Export Center**: 1-click browser download of CSV (sanitized against formula injection) and JSON datasets. |

---

## 🏗️ Architecture

```
RestaurantScraper/
├── data/
│   └── menus.db              # SQLite database (stores restaurants, items, assets, logs)
├── exports/
│   ├── menu_items.csv        # Excel-ready CSV export with UTF-8 BOM
│   └── restaurants.json      # Structured hierarchical JSON dataset
├── scraper/
│   ├── browser.py            # Playwright Chromium headless engine & network sniffer
│   ├── cli.py                # Typer + Rich interactive CLI
│   ├── config.py             # Coordinate anchors (1Borneo, Alamesra), paths, rates
│   ├── db.py                 # SQLite CRUD, fuzzy deduplication, organized views
│   ├── discovery.py          # OpenStreetMap Overpass & Google Places discovery
│   ├── extract_delivery.py   # Passive JSON sniffer & recursive catalog parser
│   ├── extract_website.py    # Website crawler (JSON-LD, microdata, plain heuristics)
│   ├── http_client.py        # Polite rate-limited HTTP client
│   ├── runner.py             # Unified scraper orchestration
│   ├── security.py           # SSRF protection, URL sanitization, CSV formula defense
│   ├── server.py             # Local HTTP server and REST API (zero extra dependencies)
│   └── ui/
│       └── index.html        # Modern dark-mode single-page local GUI
├── tests/
│   ├── test_cli.py           # CLI commands test suite
│   ├── test_scraper.py       # Scraper extraction & deduplication tests
│   ├── test_security.py      # SSRF & sanitization security tests
│   └── test_server.py        # Local GUI HTTP server & REST endpoint tests
├── pyproject.toml            # Hatchling build specification & script entrypoints
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🚀 Quick Setup

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -e .
playwright install chromium
```

---

## 💻 CLI Usage

### Launch Local Web GUI
```bash
restaurantscraper ui
# or: python -m scraper ui
# Launches local dashboard on http://127.0.0.1:8765 and opens your default browser
```

### Run Scraper on a URL
```bash
# Scrape GrabFood restaurant menu
restaurantscraper scrape "https://food.grab.com/my/en/restaurant/sushi-king-1borneo-hypermall-delivery/1-CYWJGEEFSEVKEA"

# Scrape with headless browser rendering
restaurantscraper scrape "https://restaurant-website.com" --render

# Override name, area, or cuisine
restaurantscraper scrape "https://food.grab.com/..." --name "Sushi King" --area 1borneo --cuisine "Japanese"
```

### Inspect Database in Organized Views
```bash
# List restaurants with menu metrics
restaurantscraper db list

# Filter by area or cuisine
restaurantscraper db list --area 1borneo --cuisine "Japanese"

# Search by restaurant name, address, or item
restaurantscraper db list --search "laksa"

# Deep inspection of a restaurant & its categorized menu
restaurantscraper db view "After 10 Cafe"
# or inspect by ID:
restaurantscraper db view 24

# View summary coverage statistics
restaurantscraper stats
```

### Discover Venues Around 1Borneo / Alamesra
```bash
# Scan OpenStreetMap Overpass API (free, no API key needed)
restaurantscraper discover --source osm
```

### Export Datasets
```bash
restaurantscraper export
# Generates exports/menu_items.csv and exports/restaurants.json
```

---

## 🌐 Local Web GUI (`restaurantscraper ui`)

The local GUI is served locally using Python's standard `http.server.ThreadingHTTPServer` on `http://127.0.0.1:8765`:

- **Database Explorer**:
  - Search across restaurant names, addresses, and menu item titles.
  - Filter by area (1Borneo Hypermall, Alamesra Plaza) and menu status.
  - Click **Inspect Menu** on any venue to open the organized modal catalog grouped by categories (e.g. Rice, Beverages, Mains) with prices and descriptions.
- **Scraper Studio**:
  - Direct URL input with platform detection (GrabFood, foodpanda, custom website).
  - Terminal-style live log execution output with real-time timers.
  - Instant scraped items preview table.
- **Export Center**:
  - 1-click browser download for `menu_items.csv` and `restaurants.json`.
  - Regenerate local disk files button.

---

## 🧪 Running Tests

The test suite tests extraction, security sanitization, CLI commands, and the server REST API:

```bash
pytest tests
```

---

## 🛡️ Responsible Scraping

- Respects `robots.txt` and applies rate-limiting (2s delay per host).
- Passive network response sniffing prevents aggressive crawling.
- Automatic fuzzy deduplication prevents duplicate restaurant entries.
- CSV exports are sanitized against formula injection (`=`, `+`, `-`, `@`).

---

## 📄 License

MIT License.
