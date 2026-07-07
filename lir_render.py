#!/usr/bin/env python3
"""
Leadership Insight Report — PDF render path.
Data Contract Section 6: true A4 portrait, print path (headless Chromium
print-to-PDF), live selectable text layer, embedded fonts, < 2 MB.
"""
import asyncio

async def render_lir_pdf_async(html: str) -> bytes:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            # A4 portrait at 96 dpi = 794 x 1123 px (matches .page containers)
            page = await browser.new_page(viewport={"width": 794, "height": 1123})
            await page.set_content(html, wait_until="networkidle", timeout=60000)
            # The bundle unpacks assets and renders the x-dc component async.
            await page.wait_for_selector("div.page", timeout=30000)
            await page.evaluate("document.fonts.ready")
            # Freeze any animations/transitions before capture
            await page.add_style_tag(content="*,*::before,*::after{animation:none !important;transition:none !important;}")
            await page.wait_for_timeout(250)
            pdf = await page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,  # honours @page { size: A4; margin: 0 }
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            return pdf
        finally:
            await browser.close()

def render_lir_pdf(html: str) -> bytes:
    return asyncio.run(render_lir_pdf_async(html))

if __name__ == "__main__":
    import sys
    html = open(sys.argv[1]).read()
    out = sys.argv[2] if len(sys.argv) > 2 else "out.pdf"
    pdf = render_lir_pdf(html)
    open(out, "wb").write(pdf)
    print(out, len(pdf), "bytes")
