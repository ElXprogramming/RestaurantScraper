import json
import threading
import time
import urllib.request
from scraper.server import RestaurantScraperAPIHandler, ThreadingHTTPServer


def test_server_api_endpoints():
    server = ThreadingHTTPServer(("127.0.0.1", 9922), RestaurantScraperAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)

    try:
        # 1. Status endpoint
        res = urllib.request.urlopen("http://127.0.0.1:9922/api/status")
        assert res.status == 200
        data = json.loads(res.read())
        assert data["status"] == "online"
        assert "stats" in data

        # 2. Restaurants list endpoint
        res_list = urllib.request.urlopen("http://127.0.0.1:9922/api/restaurants?limit=5")
        assert res_list.status == 200
        data_list = json.loads(res_list.read())
        assert "restaurants" in data_list
        assert len(data_list["restaurants"]) > 0

        # 3. GUI HTML endpoint
        res_html = urllib.request.urlopen("http://127.0.0.1:9922/")
        assert res_html.status == 200
        html = res_html.read().decode("utf-8")
        assert "RestaurantScraper" in html
        assert "Scraper Studio" in html

        # 4. CSV download endpoint
        res_csv = urllib.request.urlopen("http://127.0.0.1:9922/api/export/csv")
        assert res_csv.status == 200
        assert "attachment" in res_csv.headers.get("Content-Disposition", "")
        csv_bytes = res_csv.read()
        assert len(csv_bytes) > 0

        # 5. JSON download endpoint
        res_json = urllib.request.urlopen("http://127.0.0.1:9922/api/export/json")
        assert res_json.status == 200
        assert "attachment" in res_json.headers.get("Content-Disposition", "")

        # 6. Selected CSV download endpoint
        res_sel_csv = urllib.request.urlopen("http://127.0.0.1:9922/api/export/csv?ids=24")
        assert res_sel_csv.status == 200
        assert "attachment" in res_sel_csv.headers.get("Content-Disposition", "")
        sel_csv_text = res_sel_csv.read().decode("utf-8-sig")
        assert "After 10 Cafe" in sel_csv_text

        # 7. Selected JSON download endpoint
        res_sel_json = urllib.request.urlopen("http://127.0.0.1:9922/api/export/json?ids=24")
        assert res_sel_json.status == 200
        sel_json_data = json.loads(res_sel_json.read().decode("utf-8"))
        assert len(sel_json_data) == 1
        assert sel_json_data[0]["name"] == "After 10 Cafe"
    finally:
        server.shutdown()
        server.server_close()


def test_server_scrape_endpoint(monkeypatch):
    import scraper.server as server_mod

    captured = {}

    def fake_run_scrape(**kwargs):
        captured.update(kwargs)
        return {
            "success": True,
            "restaurantId": 999,
            "restaurantName": "Test Cafe",
            "itemsCount": 1,
            "items": [{"name": "Teh Tarik", "price": 3.5, "category": "Drinks"}],
        }

    server = ThreadingHTTPServer(("127.0.0.1", 0), RestaurantScraperAPIHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        # Verify real run_scrape symbol resolves cleanly without NameError
        blocked_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/scrape",
            data=json.dumps({"url": "http://127.0.0.1:1/blocked"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        blocked_res = urllib.request.urlopen(blocked_req)
        assert blocked_res.status == 200
        blocked_payload = json.loads(blocked_res.read().decode("utf-8"))
        assert blocked_payload["success"] is False
        assert "security policy" in blocked_payload["error"]

        monkeypatch.setattr(server_mod, "run_scrape", fake_run_scrape)

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/scrape",
            data=json.dumps({
                "url": "https://food.grab.com/my/en/restaurant/test-cafe/1-ABC",
                "name": "Test Cafe",
                "area": "1borneo",
                "cuisine": "Malaysian",
                "render": True,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        res = urllib.request.urlopen(req)
        assert res.status == 200
        payload = json.loads(res.read().decode("utf-8"))
        assert payload["success"] is True
        assert payload["restaurantName"] == "Test Cafe"
        assert captured["url"] == "https://food.grab.com/my/en/restaurant/test-cafe/1-ABC"
        assert captured["render"] is True
        assert captured["save_sqlite"] is True
    finally:
        server.shutdown()
        server.server_close()
