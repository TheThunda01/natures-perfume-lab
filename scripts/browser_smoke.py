"""Optional Chromium checks for the static explorer; no network assets required.

Install Playwright separately and supply Chromium (or run playwright install
chromium). This script serves web/ on a loopback-only temporary HTTP server unless
--url is supplied. It creates screenshots only with --screenshots DIRECTORY.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check(url: str, screenshots: Path | None, executable: str | None) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise SystemExit("Optional dependency missing: install playwright to run browser checks.") from error
    errors, remote_requests = [], []
    origin = urlparse(url).netloc
    with sync_playwright() as playwright:
        options = {"headless": True, "args": ["--no-sandbox"]}
        if executable:
            options["executable_path"] = executable
        browser = playwright.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: remote_requests.append(request.url)
                    if urlparse(request.url).scheme in {"http", "https"}
                    and urlparse(request.url).netloc != origin else None)
            page.goto(url, wait_until="networkidle")
            assert not page.locator("#data-error").is_visible(), "Generated data did not load"
            assert page.locator(".molecule-choice").count() == 3
            assert page.locator(".atom-button").count() == 10
            assert page.locator("#structure-2d svg").count() == 1
            assert page.locator(".reaction-card").count() == 2
            assert page.locator(".enzyme-card").count() == 2
            assert page.locator(".alignment-block").count() > 1
            assert page.locator(".evidence-item a").count() >= 4
            page.get_by_role("button", name="Select carbon atom 3", exact=True).focus()
            page.keyboard.press("Enter")
            assert "Carbon 3 selected" in page.locator("#atom-status").inner_text()
            for molecule in ["limonene", "linalool", "gpp"]:
                page.locator(f'.molecule-choice[data-id="{molecule}"]').click()
                assert page.locator(".atom-button").count() == 10
                assert "Carbon 3 selected" in page.locator("#atom-status").inner_text()
                assert page.get_by_role("button", name="Select carbon atom 3", exact=True).get_attribute("aria-pressed") == "true"
                assert page.locator("#structure-2d .atom-halo").count() == 1, "Selected carbon needs an exact 2D highlight"
                assert not page.locator("#view-3d").is_disabled()

            page.locator('.molecule-choice[data-id="limonene"]').click()
            if screenshots:
                page.locator("#explorer").scroll_into_view_if_needed()
                page.screenshot(path=str(screenshots / "explorer-2d.png"))
            page.locator("#view-3d").click()
            page.wait_for_timeout(100)
            canvas = page.locator("#molecule-canvas")
            before = canvas.evaluate("(c) => c.toDataURL()")
            page.locator("#rotation-y").focus()
            page.keyboard.press("ArrowRight")
            after = canvas.evaluate("(c) => c.toDataURL()")
            assert before != after, "Keyboard rotation did not redraw the model"
            rect = canvas.bounding_box()
            page.mouse.move(rect["x"] + 100, rect["y"] + 100)
            page.mouse.down()
            page.mouse.move(rect["x"] + 160, rect["y"] + 130, steps=8)
            page.mouse.up()
            assert after != canvas.evaluate("(c) => c.toDataURL()"), "Drag rotation did not redraw the model"
            if screenshots:
                page.locator("#explorer").scroll_into_view_if_needed()
                page.screenshot(path=str(screenshots / "explorer-3d.png"))
            page.locator("#view-2d").click()
            page.locator("#clear-atom").click()
            assert page.locator('.atom-button[aria-pressed="true"]').count() == 0
            route = page.locator('.route-link[data-product="linalool"]')
            route.focus()
            page.keyboard.press("Enter")
            assert page.locator('.molecule-choice[data-id="linalool"]').get_attribute("aria-pressed") == "true"
            page.locator('.molecule-choice[data-id="limonene"]').click()
            page.locator("#mapping-details summary").focus()
            page.keyboard.press("Enter")
            assert page.locator("#mapping-details").get_attribute("open") is not None
            assert "swap" in page.locator("#mapping-description").inner_text().lower()
            page.keyboard.press("Enter")
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(500)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            if screenshots:
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.screenshot(path=str(screenshots / "desktop-top.png"))
            for width in [375, 320, 768]:
                page.set_viewport_size({"width": width, "height": 900})
                page.evaluate("window.scrollTo(0,0)")
                for molecule in ["gpp", "limonene", "linalool"]:
                    page.locator(f'.molecule-choice[data-id="{molecule}"]').click()
                    assert page.locator(".atom-button").count() == 10
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Overflow at {width}px with {molecule}"
                if width == 375 and screenshots:
                    page.locator('.molecule-choice[data-id="limonene"]').click()
                    page.evaluate("window.scrollTo(0,0)")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                    page.screenshot(path=str(screenshots / "mobile-top.png"))
            assert not errors, errors
            assert not remote_requests, f"Unexpected external asset requests: {remote_requests}"
            return {"result": "passed", "molecules": 3, "carbon_buttons_per_molecule": 10,
                    "persistent_mapped_selection": True, "keyboard_selection": True,
                    "keyboard_3d_rotation": True, "pointer_3d_rotation": True,
                    "keyboard_route_navigation": True, "mapping_explanation": True,
                    "alignment_rendered": True, "source_links": True,
                    "viewport_widths": [1440, 768, 375, 320],
                    "page_errors": errors, "external_asset_requests": remote_requests}
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Use an already running copy of the explorer")
    parser.add_argument("--screenshots", type=Path, help="Optional output directory for screenshots")
    parser.add_argument("--chromium", help="Chromium executable; otherwise use a system or Playwright installation")
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    server = None
    try:
        url = args.url
        if not url:
            handler = partial(QuietHandler, directory=str(ROOT / "web"))
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            url = f"http://127.0.0.1:{server.server_port}/"
        executable = args.chromium or shutil.which("chromium") or shutil.which("google-chrome")
        print(json.dumps(check(url, args.screenshots, executable), indent=2))
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
