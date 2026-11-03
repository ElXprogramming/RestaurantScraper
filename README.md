# 🍽️ RestaurantScraper

> **High-performance restaurant menu scraper, organized SQLite database explorer, and CSV/JSON export tool with both a modern CLI and local Web GUI.**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Database](https://img.shields.io/badge/Storage-SQLite3%20%28WAL%29-green.svg)](https://sqlite.org)
[![CLI Framework](https://img.shields.io/badge/CLI-Typer%20%2B%20Rich-cyan.svg)](https://typer.tiangolo.com)
[![Headless Engine](https://img.shields.io/badge/Engine-Playwright%20Chromium-red.svg)](https://playwright.dev)
[![Local First](https://img.shields.io/badge/Privacy-100%25%20Local--First-emerald.svg)](#architecture)

---

## 📖 Overview

**RestaurantScraper** is a local-first menu extraction system engineered to harvest, deduplicate, and catalog food menus from dynamic delivery platforms (GrabFood, foodpanda) and restaurant websites.

Traditional HTML scrapers fail against modern single-page applications (like GrabFood's Next.js frontend). RestaurantScraper overcomes this by utilizing a **passive network response sniffer** in headless Playwright Chromium that intercepts internal JSON payloads in real-time, normalizes currency from minor units to Ringgit (MYR), and intelligently merges venues using fuzzy name matching and geographic proximity.

The system is designed with zero external deployment bloat: you can run it directly from your terminal with a rich CLI or open the built-in, zero-dependency local Web GUI in your browser.

---

## ⚡ The 3 Core Pillars

| Function | CLI Command | Local Web GUI (`http://127.0.0.1:8765`) |
| :--- | :--- | :--- |
| **1. Universal Scraper** | `restaurantscraper scrape <URL>` | **Scraper Studio**: Paste URLs, select options, view live streaming terminal logs, and inspect immediate parsed item previews. |
| **2. Database Explorer** | `restaurantscraper db list` / `db view <ID>` | **Database Explorer**: Instant search across restaurants/items, area filtering, and categorized menu modal catalogs. |
| **3. Clean Data Export** | `restaurantscraper export` | **Export Center**: 1-click browser download of sanitized Excel-ready CSV and structured hierarchical JSON. |

---

## 📸 User Interface Overview

RestaurantScraper includes a zero-dependency, local-first Web GUI built with vanilla JavaScript and Tailwind CSS that connects directly to the embedded SQLite database and Python scraper engine.

### 🗄️ Database Explorer & Selective Export
Browse saved restaurants, filter by delivery area, select individual venues with checkboxes, and trigger selective multi-venue exports directly from the sticky action bar.
![Database Explorer](docs/images/database_explorer.png)

### 📋 Organized Menu Inspector Modal
Click **Inspect Menu** on any restaurant to browse dishes organized by category (e.g. Mains, Beverages, Desserts), search items, inspect ingredients & pricing in MYR, and export that single restaurant with one click.
![Menu Inspector Modal](docs/images/menu_inspector_modal.png)

### 🕷️ Universal Scraper Studio
Scrape GrabFood and foodpanda menus visually with quick URL presets, custom area/cuisine overrides, live real-time execution logs, and immediate item previews.
![Scraper Studio](docs/images/scraper_studio.png)

### 📦 Data Export Center
Export your collected data in clean, sanitized CSV (RFC 4180 compliant with formula injection protection) or nested hierarchical JSON. Choose between exporting the entire catalog or only selected restaurants.
![Export Center](docs/images/export_center.png)

---

## 📦 Complete Installation Tutorial (Step-by-Step)

Follow this thorough guide to install and run RestaurantScraper on your machine from scratch.

### Step 1: Prerequisites
Ensure you have the following installed on your machine:
- **Git**: [git-scm.com](https://git-scm.com/)
- **Python 3.11, 3.12, 3.13, or 3.14**: Run `python3 --version` to verify.

---

### Step 2: Clone the Repository from GitHub

Open your terminal (or Command Prompt / PowerShell on Windows) and clone the repository:

```bash
# Clone the repository
git clone https://github.com/ElXprogramming/RestaurantScraper.git

# Enter the project directory
cd RestaurantScraper
```

---

### Step 3: Create a Virtual Environment

It is best practice to run RestaurantScraper within an isolated virtual environment:

```bash
# Create a virtual environment named .venv
python3 -m venv .venv
```

---

### Step 4: Activate the Virtual Environment

Activate the environment based on your operating system:

* **Linux / macOS (Bash or Zsh)**:
  ```bash
  source .venv/bin/activate
  ```

* **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If PowerShell gives an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first)*

* **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

* **Fish Shell**:
  ```fish
  source .venv/bin/activate.fish
  ```

Once activated, your terminal prompt will be prefixed with `(.venv)`.

---

### Step 5: Install Python Dependencies

Install all core dependencies and install the project in editable mode:

```bash
# Install required packages (typer, rich, playwright, beautifulsoup4, requests, etc.)
pip install -r requirements.txt

# Install the restaurantscraper command-line tool into your environment
pip install -e .
```

---

### Step 6: Install Playwright Headless Chromium

The scraper uses Playwright Chromium to intercept background JSON network traffic from GrabFood and render JavaScript-heavy restaurant websites:

```bash
# Install the Chromium browser binary
playwright install chromium
```

> **Note for Linux Server / Ubuntu users**: If your system is missing system graphical libraries, run:
> ```bash
> playwright install --with-deps chromium
> ```

---

### Step 7: (Optional) Configuration

RestaurantScraper works immediately out of the box with default settings. Optionally, you can configure custom settings by copying `.env.example`:

```bash
cp .env.example .env
```

Available environment variables:
- `GOOGLE_PLACES_API_KEY`: *(Optional)* Only needed if you want to discover venues using Google Places API in addition to OpenStreetMap.
- `SCRAPER_UA`: *(Optional)* Custom User-Agent string for responsible web requests.
- `MENU_DB`: *(Optional)* Path to your SQLite database file (defaults to `data/menus.db`).

---

## 🎯 How to Use the Scraper

You have two interfaces to choose from: the **Local Web GUI** and the **Command-Line Interface (CLI)**.

---

### Method A: Using the Local Web GUI (Recommended)

To launch the modern interactive browser interface, run:

```bash
restaurantscraper ui
# Or alternatively: python3 -m scraper ui
```

Your default web browser will automatically open to:
```
http://127.0.0.1:8765
```

The GUI consists of three dedicated tabs:

#### 1. ⚡ Scraper Studio Tab
1. Paste any **GrabFood**, **foodpanda**, or **restaurant website** URL into the Target URL field.
   * *Example GrabFood URL*: `https://food.grab.com/my/en/restaurant/sushi-king-1borneo-hypermall-delivery/1-CYWJGEEFSEVKEA`
2. *(Optional)* Click **Optional Overrides** to specify custom restaurant name, area (`1borneo` or `alamesra`), or cuisine tags.
3. Check **Use Headless Chromium Rendering** if targeting JavaScript-heavy websites.
4. Click **🚀 Run Scraper**.
5. Watch the real-time execution log. Once finished, a summary card will appear showing the restaurant details, address, rating, and an immediate preview table of all scraped menu items and prices in Ringgit (MYR). The items are automatically saved into your SQLite database.

#### 2. 📂 Database Explorer Tab
1. Browse all stored restaurants (the included dataset comes pre-loaded with **25 restaurants** and **1,325 items** around 1Borneo and Alamesra).
2. **Selective Export via Checkboxes**:
   * Click checkboxes on any individual restaurants (or check the header checkbox to select all).
   * A selection action bar appears immediately: click **📊 Export Selected CSV** or **📦 Export Selected JSON** to export only your chosen venues.
3. **Instant Search**: Type in the search box to filter restaurants and menu items in real-time.
4. **Filter**: Filter by area (*1Borneo Hypermall*, *Alamesra Plaza*) or menu completeness (*Has Menu Items*, *Needs Scraping*).
5. **Sort**: Sort by rating, total items, lowest average price, or alphabetical order.
6. **Inspect Menu & Single-Restaurant Export**: Click **Inspect Menu** on any row to open the full modal catalog:
   * Click **📊 Export CSV** or **📦 Export JSON** in the modal header to export only that specific restaurant's menu.
   * View full address, operating hours, coordinates, and direct links.
   * Click category pills (e.g. *Rice*, *Beverages*, *Set Nasi*, *Noodles*) to filter sections.
   * Search for specific dishes within the restaurant's menu.

#### 3. 📤 Export Center Tab
1. **Choose Export Scope**:
   * **All Restaurants**: Export the entire database (all 25 venues and 1,325 items).
   * **Selected Restaurants Only**: Export only the venues currently selected in Database Explorer.
2. **Download CSV**: Click **⬇ Download CSV** for an Excel-ready dataset with UTF-8 BOM encoding and protection against spreadsheet formula injection.
3. **Download JSON**: Click **⬇ Download JSON** for a clean nested JSON catalog.
4. **Write to Disk**: Click **💾 Write to exports/ directory** to write updated files directly into your local `exports/` folder (also respects your selection scope).

---

### Method B: Using the Command-Line Interface (CLI)

RestaurantScraper provides a Typer-powered CLI with Rich terminal formatting.

#### 1. Scrape a Restaurant URL
Scrape a GrabFood delivery page, foodpanda page, or restaurant website directly from your terminal:

```bash
# Scrape a GrabFood restaurant menu
restaurantscraper scrape "https://food.grab.com/my/en/restaurant/sushi-king-1borneo-hypermall-delivery/1-CYWJGEEFSEVKEA"

# Scrape with headless browser rendering for JS websites
restaurantscraper scrape "https://www.example-restaurant.com" --render

# Scrape with custom name and area overrides
restaurantscraper scrape "https://food.grab.com/..." --name "Sushi King" --area 1borneo --cuisine "Japanese"
```

#### 2. View Summary Statistics
Check the database status, restaurant count, total menu items, price range, and source breakdown:

```bash
restaurantscraper stats
```

#### 3. List Restaurants in the Database
Display an organized Rich table of restaurants:

```bash
# List top 20 restaurants
restaurantscraper db list --limit 20

# Filter by area
restaurantscraper db list --area 1borneo

# Search by restaurant name, cuisine, address, or item keyword
restaurantscraper db list --search "ayam"

# Sort by rating, items count, or average price
restaurantscraper db list --sort rating
restaurantscraper db list --sort items
restaurantscraper db list --sort price
```

#### 4. Deep Inspection of a Specific Restaurant
Inspect full restaurant details and its categorized menu:

```bash
# Inspect by restaurant name
restaurantscraper db view "After 10 Cafe"

# Or inspect by restaurant ID
restaurantscraper db view 24
```

This outputs:
- Restaurant address, rating, operating hours, and GrabFood/website links.
- Tables for each menu category (e.g. *Ayam Goreng Crispy*, *Set Nasi*, *Beverages*).
- Individual item names, prices in Ringgit (MYR), descriptions, and source tags.

#### 5. Discover Venues in an Area
Query OpenStreetMap Overpass (free, no API key required) to discover eateries around 1Borneo and Alamesra:

```bash
restaurantscraper discover --source osm
```

#### 6. Attach or Update a URL
Quickly attach a GrabFood link, foodpanda link, or website to a restaurant:

```bash
restaurantscraper add-link "Sushi King" "https://food.grab.com/my/en/restaurant/..."
```

#### 7. Export the Database (All or Selected)
Export either the entire database or only specific selected restaurants to CSV and JSON:

```bash
# Export all restaurants in the database
restaurantscraper export

# Export only specific restaurant IDs (e.g. ID 24 and ID 19)
restaurantscraper export --ids 24,19

# Export by restaurant name filter
restaurantscraper export --name "Sushi King"

# Export by area (e.g. 1borneo or alamesra)
restaurantscraper export --area 1borneo

# Export to a custom output directory
restaurantscraper export --ids 24 --out-dir my_custom_exports/
```
Outputs:
- `exports/menu_items.csv`
- `exports/restaurants.json`

---

## 🔬 How the GrabFood Headless Sniffer Works

GrabFood's web client is built with Next.js and renders menus dynamically on client-side hydration. Standard HTTP crawlers (like `curl` or `requests`) only receive an empty HTML shell.

RestaurantScraper implements a specialized passive network sniffer:

1. **Geolocation Lock**: Headless Chromium launches with Kota Kinabalu coordinates (`6.0360, 116.1297`) and `en-MY` locale to bypass Grab's regional delivery locks.
2. **Passive Sniffing**: Uses Playwright's `page.on("response")` event to listen for asynchronous JSON API payloads returned by Grab's gateway.
3. **Recursive Catalog Walker**: Recursively traverses nested categories, sections, item variations, and modifiers (`_walk()` function in [`scraper/extract_delivery.py`](file:///home/eldion/RestaurantScraper/scraper/extract_delivery.py)).
4. **Price Normalization**: Converts GrabFood's integer minor unit prices (`priceInMinorUnit / 100`) to standard Ringgit floats (e.g. `1290` -> `RM 12.90`).
5. **Fuzzy Deduplication**: When adding restaurants, the engine calculates name similarity (via `difflib.SequenceMatcher`) and geographical distance (via the **Haversine formula** <= 150m) to automatically merge records instead of creating duplicates.

---

## 🧪 Running the Offline Test Suite

RestaurantScraper comes with a comprehensive test suite testing extraction logic, security sanitization, CLI commands, and the local GUI server:

```bash
# Run all tests
pytest tests
```

Expected output:
```
tests/test_cli.py ......                                                 [ 22%]
tests/test_scraper.py ............                                       [ 66%]
tests/test_security.py ........                                          [ 96%]
tests/test_server.py .                                                   [100%]

============================== 27 passed in 1.31s ==============================
```

---

## ❓ Troubleshooting & FAQ

#### 1. `playwright._impl._errors.Error: Executable doesn't exist`
You need to install the Chromium browser binary used by Playwright. Run:
```bash
playwright install chromium
```

#### 2. Linux server: missing shared libraries (`libnss3.so`, etc.)
If running on an Ubuntu or Debian server without desktop packages:
```bash
playwright install --with-deps chromium
```

#### 3. Command `restaurantscraper: command not found`
Ensure your virtual environment is activated (`source .venv/bin/activate`), or execute the package directly using Python:
```bash
python3 -m scraper ui
# or: python3 -m scraper scrape "URL"
```

#### 4. Excel opens the CSV with corrupted characters
The CSV exporter automatically writes a **UTF-8 BOM** (`utf-8-sig`) header, ensuring Microsoft Excel, Apple Numbers, and LibreOffice Calc render non-ASCII characters correctly.

#### 5. Formula Injection Defense
Any cell starting with dangerous characters (`=`, `+`, `-`, `@`) is safely prefixed with an apostrophe (`'`) by [`scraper/security.py`](file:///home/eldion/RestaurantScraper/scraper/security.py) to prevent CSV Formula Injection attacks when opening files in spreadsheet software.

---

## 🛡️ Responsible Scraping Practices

- **Rate-Limiting**: A polite delay (default: 2.0s per host) is enforced between requests.
- **Robots Exclusion**: Standard `robots.txt` directives are parsed and respected.
- **Academic & Research Use**: Cite your data sources when using this dataset for research or reporting.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
