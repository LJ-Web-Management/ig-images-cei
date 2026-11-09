"""Render a CEI Career Spotlight image (1080x1350 PNG) from a JSON spec.

Usage: python3 template/render.py spec.json images/YYYY-MM-DD-slug.png

spec.json keys:
  career, tagline, summary, median_pay, growth_label, growth,
  time_to_train, bullets (list of 3 short strings), source_note
All figures must come from the career's page on cei.ictraining.us.
"""
import html
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))


def build(spec):
    tpl = open(os.path.join(HERE, "career_spotlight.html"), encoding="utf-8").read()
    fields = dict(spec)
    fields["bullets"] = "".join(f"<li>{html.escape(b)}</li>" for b in spec["bullets"])
    for key, value in fields.items():
        if key != "bullets":
            value = html.escape(str(value))
        tpl = tpl.replace("{{" + key + "}}", value)
    return tpl


def find_chrome():
    for path in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if os.path.exists(path):
            return path
    return None


def main(spec_path, out_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    page_html = build(spec)
    tmp = os.path.abspath(out_path) + ".html"
    open(tmp, "w", encoding="utf-8").write(page_html)
    with sync_playwright() as p:
        chrome = find_chrome()
        browser = p.chromium.launch(executable_path=chrome) if chrome else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.goto("file://" + tmp)
        page.wait_for_timeout(500)
        bottom = page.evaluate("document.querySelector('.footer').getBoundingClientRect().bottom")
        overflow = page.evaluate(
            "[...document.querySelectorAll('.wordmark .a, .cta')].some(e => e.scrollWidth > e.clientWidth)"
        )
        page.screenshot(path=out_path)
        browser.close()
    os.remove(tmp)
    if bottom > 1300 or overflow:
        sys.exit(f"Layout overflow (footer bottom {bottom}px): shorten the text and re-render.")
    print(f"Rendered {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
