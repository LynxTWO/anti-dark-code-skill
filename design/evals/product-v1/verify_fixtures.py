"""Verify seeded behavior and clean controls in Chromium; no model evaluation."""
import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
import json
from pathlib import Path
import platform
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def verify():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "fixtures")))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    observations = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                browser_version = browser.version
                for variant in ("broken", "clean"):
                    expected_clean = variant == "clean"
                    context = browser.new_context()
                    try:
                        page = context.new_page()
                        url = f"http://127.0.0.1:{server.server_port}/{variant}/index.html"
                        page.goto(url)
                        note = "A note with Unicode: caf\u00e9 \u4e2d"
                        page.locator("#draft").fill(note)
                        page.locator("#save").click()
                        page.reload()
                        assert page.locator("#draft").input_value() == note
                        observations.append({"fixture": variant, "case": "unicode-persistence", "contract_holds": True})
                        page.evaluate("() => { window.originalSet = Storage.prototype.setItem; Storage.prototype.setItem = function() { throw new Error('synthetic quota'); }; }")
                        page.locator("#draft").fill("Keep this draft")
                        page.locator("#save").click()
                        truthful = page.locator("#status").inner_text() != "Saved"
                        assert truthful == expected_clean
                        assert page.locator("#draft").input_value() == "Keep this draft"
                        observations.append({"fixture": variant, "case": "false-save-success", "contract_holds": truthful})
                        page.evaluate("() => { Storage.prototype.setItem = window.originalSet; }")
                        page.locator("#settings").click()
                        refused = page.evaluate("localStorage.getItem('notes-analytics')") == "no"
                        assert refused == expected_clean
                        observations.append({"fixture": variant, "case": "analytics-refusal-ignored", "contract_holds": refused})
                        page.evaluate("localStorage.setItem('unrelated', 'preserve')")
                        page.locator("#clear").click()
                        preserved = page.evaluate("localStorage.getItem('unrelated')") == "preserve"
                        assert preserved == expected_clean
                        observations.append({"fixture": variant, "case": "clear-unrelated-data", "contract_holds": preserved})
                        undo = page.locator("#undo").count() == 1
                        if undo:
                            page.locator("#undo").click()
                            assert page.locator("#draft").input_value() == "Keep this draft"
                        assert undo == expected_clean
                        observations.append({"fixture": variant, "case": "clear-without-undo", "contract_holds": undo})
                        page.reload()
                        page.locator("#draft").focus()
                        page.keyboard.press("Tab")
                        keyboard = page.evaluate("document.activeElement.id") == "save"
                        assert keyboard == expected_clean
                        if keyboard:
                            page.locator("#draft").fill("Keyboard save")
                            page.locator("#draft").focus()
                            page.keyboard.press("Tab")
                            page.keyboard.press("Enter")
                            assert page.evaluate("localStorage.getItem('note')") == "Keyboard save"
                        observations.append({"fixture": variant, "case": "keyboard-actions", "contract_holds": keyboard})
                        price = "$60" in page.locator("#price").inner_text()
                        assert price == expected_clean
                        observations.append({"fixture": variant, "case": "hidden-annual-total", "contract_holds": price})
                        neutral = page.locator("#decline").inner_text() == "Keep using local notes"
                        assert neutral == expected_clean
                        observations.append({"fixture": variant, "case": "shaming-refusal", "contract_holds": neutral, "method": "expected copy; comprehension untested"})
                        context.add_init_script("Storage.prototype.getItem = function() { throw new Error('synthetic read failure'); }")
                        page.reload()
                        page.locator("#draft").fill("Draft after read failure")
                        page.locator("#save").click()
                        recovered = page.locator("#status").inner_text() == "Saved"
                        assert recovered == expected_clean
                        observations.append({"fixture": variant, "case": "startup-storage-failure", "contract_holds": recovered})
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()
    files = [ROOT / "cases.json", Path(__file__), *sorted((ROOT / "fixtures").rglob("*.html"))]
    return {"schema": 1, "claim": "Fixture observations only; not agent compliance or participant validation.",
        "agent_trials_executed": 0, "os": platform.platform(), "python": platform.python_version(),
        "playwright": version("playwright"), "chromium": browser_version,
        "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
        "observations": observations, "complete": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a new evidence file")
    result = verify()
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2, ensure_ascii=True)
        output.write("\n")
    print(f"{len(result['observations'])} browser fixture observations verified; 0 agent trials.")
