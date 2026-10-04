#!/usr/bin/env python3
"""Render the field brief to PDF the way its provenance record describes.

Usage: python render-brief-pdf.py --html brief/anti-dark-code-brief.html --out /tmp/brief.pdf

Uses Playwright Chromium in print media with the page size the brief's own
@page rule declares. Prints a JSON line with the generator string, the raw
PDF digest and the byte count. The raw digest changes on every render because
Chromium restamps timestamps; compare renders with
scripts/adc.py's normalized_pdf_sha256 instead.
"""
import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--html", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    html = Path(args.html).resolve()
    out = Path(args.out).resolve()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(html.as_uri(), wait_until="load")
        page.emulate_media(media="print")
        page.pdf(
            path=str(out),
            prefer_css_page_size=True,
            print_background=True,
            display_header_footer=False,
        )
        chromium = browser.version
        browser.close()
    generator = (
        f"Playwright {version('playwright')} / Chromium {chromium} "
        f"on {platform.system()} {platform.machine()}"
    )
    print(json.dumps({
        "generator": generator,
        "pdf_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "bytes": out.stat().st_size,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
