"""Local Web GUI HTTP Server and REST API for RestaurantScraper.
Zero-dependency server using Python's standard http.server.
"""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
import urllib.parse
import webbrowser

from scraper import config, db, discovery
from scraper.runner import cmd_scrape

logger = logging.getLogger("scraper.server")

# In-memory job state for active background operations
SCRAPE_JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()


class RestaurantScraperAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request handler serving the Local GUI and REST endpoints."""

    server_version = "RestaurantScraperServer/0.2.0"

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy request logs to keep terminal clean."""
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html_content: str, status: int = HTTPStatus.OK) -> None:
        payload = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_file_download(self, content: bytes, filename: str, mime_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        try:
            if path in ("/", "/index.html"):
                self._serve_gui()
            elif path == "/api/status":
                self._handle_status()
            elif path == "/api/restaurants":
                self._handle_list_restaurants(query)
            elif path.startswith("/api/restaurants/"):
                rest_id = path.removeprefix("/api/restaurants/").strip()
                self._handle_restaurant_detail(rest_id)
            elif path == "/api/stats":
                self._handle_stats()
            elif path == "/api/jobs":
                self._handle_jobs()
            elif path == "/api/export/csv":
                self._handle_export_csv_download()
            elif path == "/api/export/json":
                self._handle_export_json_download()
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
        except Exception as exc:
            logger.exception("Error handling GET request %s", path)
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        try:
            if path == "/api/scrape":
                self._handle_scrape(data)
            elif path == "/api/discover":
                self._handle_discover(data)
            elif path == "/api/export":
                self._handle_export(data)
            elif path == "/api/restaurants":
                self._handle_add_or_update_link(data)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
        except Exception as exc:
            logger.exception("Error handling POST request %s", path)
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/restaurants/"):
                rest_id_str = path.removeprefix("/api/restaurants/").strip()
                if rest_id_str.isdigit():
                    conn = db.connect(config.DB_PATH)
                    success = db.delete_restaurant(conn, int(rest_id_str))
                    self._send_json({"success": success, "id": int(rest_id_str)})
                else:
                    self._send_json({"error": "Invalid restaurant ID"}, status=HTTPStatus.BAD_REQUEST)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
        except Exception as exc:
            logger.exception("Error handling DELETE request %s", path)
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # --- Route Implementations ---

    def _serve_gui(self) -> None:
        for candidate in [
            Path(__file__).parent / "ui" / "index.html",
            Path(__file__).parent.parent / "scraper" / "ui" / "index.html",
            Path(__file__).parent.parent / "index.html",
        ]:
            if candidate.exists():
                self._send_html(candidate.read_text(encoding="utf-8"))
                return
        self._send_html(
            "<h1>RestaurantScraper Local GUI</h1><p>GUI index.html not found. Check scraper/ui/index.html.</p>"
        )

    def _handle_status(self) -> None:
        conn = db.connect(config.DB_PATH)
        stats = db.get_database_stats(conn)
        self._send_json({
            "status": "online",
            "version": "0.2.0",
            "database_path": str(config.DB_PATH),
            "export_dir": str(config.EXPORT_DIR),
            "stats": stats,
        })

    def _handle_stats(self) -> None:
        conn = db.connect(config.DB_PATH)
        self._send_json(db.get_database_stats(conn))

    def _handle_list_restaurants(self, query: Dict[str, List[str]]) -> None:
        search = query.get("search", [None])[0]
        area = query.get("area", [None])[0]
        cuisine = query.get("cuisine", [None])[0]
        has_menu_val = query.get("has_menu", [None])[0]
        sort_by = query.get("sort", ["name"])[0]
        limit_val = query.get("limit", [100])[0]
        offset_val = query.get("offset", [0])[0]

        has_menu = None
        if has_menu_val is not None:
            if has_menu_val.lower() in ("true", "1", "yes"):
                has_menu = True
            elif has_menu_val.lower() in ("false", "0", "no"):
                has_menu = False

        conn = db.connect(config.DB_PATH)
        rows = db.get_restaurants_organized(
            conn,
            search=search,
            area=area,
            cuisine=cuisine,
            has_menu=has_menu,
            sort_by=sort_by,
            limit=int(limit_val) if limit_val else None,
            offset=int(offset_val) if offset_val else 0,
        )
        self._send_json({"count": len(rows), "restaurants": rows})

    def _handle_restaurant_detail(self, identifier: str) -> None:
        conn = db.connect(config.DB_PATH)
        detail = db.get_restaurant_detail(conn, identifier)
        if detail:
            self._send_json(detail)
        else:
            self._send_json({"error": "Restaurant not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_scrape(self, data: Dict[str, Any]) -> None:
        url = (data.get("url") or "").strip()
        if not url:
            self._send_json({"success": False, "error": "URL parameter is required."}, status=HTTPStatus.BAD_REQUEST)
            return

        name = data.get("name")
        render = bool(data.get("render", False))
        area = data.get("area")
        cuisine = data.get("cuisine")
        rating = data.get("rating")
        address = data.get("address")

        job_id = f"job_{int(time.time() * 1000)}"
        with JOBS_LOCK:
            SCRAPE_JOBS[job_id] = {
                "id": job_id,
                "url": url,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "result": None,
            }

        # Run synchronously or in thread based on synchronous preference
        is_async = bool(data.get("async", False))

        def _execute():
            try:
                res = run_scrape(
                    url=url,
                    name=name,
                    rating=rating,
                    cuisine=cuisine,
                    address=address,
                    area=area,
                    render=render,
                    save_sqlite=True,
                )
                with JOBS_LOCK:
                    SCRAPE_JOBS[job_id]["status"] = "completed" if res.get("success") else "failed"
                    SCRAPE_JOBS[job_id]["result"] = res
                    SCRAPE_JOBS[job_id]["finished_at"] = datetime.now().isoformat()
            except Exception as e:
                with JOBS_LOCK:
                    SCRAPE_JOBS[job_id]["status"] = "failed"
                    SCRAPE_JOBS[job_id]["error"] = str(e)
                    SCRAPE_JOBS[job_id]["finished_at"] = datetime.now().isoformat()

        if is_async:
            threading.Thread(target=_execute, daemon=True).start()
            self._send_json({"job_id": job_id, "status": "running"})
        else:
            _execute()
            job = SCRAPE_JOBS.get(job_id, {})
            result = job.get("result") or {"success": False, "error": job.get("error", "Unknown error")}
            self._send_json(result)

    def _handle_discover(self, data: Dict[str, Any]) -> None:
        source = data.get("source", "all")
        radius = int(data.get("radius", config.DEFAULT_RADIUS_M))

        conn = db.connect(config.DB_PATH)
        results = {}
        if source in ("osm", "all"):
            results["osm"] = discovery.discover_osm(conn, radius)
        if source in ("google", "all"):
            try:
                results["google"] = discovery.discover_google(conn, radius)
            except Exception as e:
                results["google_error"] = str(e)

        results["total_in_db"] = conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        self._send_json(results)

    def _handle_export(self, data: Dict[str, Any]) -> None:
        out_dir = Path(data.get("out_dir") or config.EXPORT_DIR)
        conn = db.connect(config.DB_PATH)
        res = db.export(conn, out_dir)
        self._send_json(res)

    def _handle_export_csv_download(self) -> None:
        conn = db.connect(config.DB_PATH)
        csv_content = db.export_csv_string(conn).encode("utf-8-sig")
        self._send_file_download(csv_content, "menu_items.csv", "text/csv; charset=utf-8")

    def _handle_export_json_download(self) -> None:
        conn = db.connect(config.DB_PATH)
        json_content = db.export_json_string(conn).encode("utf-8")
        self._send_file_download(json_content, "restaurants.json", "application/json; charset=utf-8")

    def _handle_add_or_update_link(self, data: Dict[str, Any]) -> None:
        name = (data.get("name") or "").strip()
        url = (data.get("url") or "").strip()
        area = data.get("area")

        if not name or not url:
            self._send_json({"error": "name and url required"}, status=HTTPStatus.BAD_REQUEST)
            return

        conn = db.connect(config.DB_PATH)
        col = (
            "grab_url" if "grab.com" in url
            else "foodpanda_url" if "foodpanda" in url
            else "website"
        )
        rows = conn.execute("SELECT id, name FROM restaurants WHERE name LIKE ?", (f"%{name}%",)).fetchall()
        if len(rows) > 1:
            self._send_json({"error": f"Multiple restaurants match '{name}'", "matches": [r["name"] for r in rows]}, status=HTTPStatus.CONFLICT)
            return

        if len(rows) == 0:
            rid = db.upsert_restaurant(conn, {"name": name, col: url, "area": area})
            self._send_json({"success": True, "action": "created", "id": rid, "name": name})
        else:
            conn.execute(f"UPDATE restaurants SET {col}=? WHERE id=?", (url, rows[0]["id"]))
            conn.commit()
            self._send_json({"success": True, "action": "updated", "id": rows[0]["id"], "name": rows[0]["name"]})

    def _handle_jobs(self) -> None:
        with JOBS_LOCK:
            # Return last 20 jobs
            jobs = list(SCRAPE_JOBS.values())[-20:]
            self._send_json({"jobs": jobs})


def start_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Launch the RestaurantScraper Local Web GUI server."""
    server = ThreadingHTTPServer((host, port), RestaurantScraperAPIHandler)
    url = f"http://{host}:{port}"

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
